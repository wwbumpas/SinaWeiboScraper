#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Author: Xuzhou Yin 
# Fork by William Bumpas


from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
import urllib
import datetime
import time as systime
from selenium.webdriver.firefox.webdriver import FirefoxProfile
import unicodecsv as csv
import random
import json
import pickle
import re
from time import gmtime, strftime
import sys  
import traceback
import os

reload(sys)  
sys.setdefaultencoding('utf8')

now = strftime("%m%d_%H%M%S", gmtime())

base_url = 'http://s.weibo.com/weibo/'
file = "query%s_" % now #make sure filename is unique

try:
	done = pickle.load(open("query_done.pkl", "rb")) 
	#If script exits mid query, this will let it pick up where it left off
	print("Loaded most recent query: %s" % str(done[-1]))
except:
	done = [] #Otherwise, start from scratch

# print(done)

failures = 0 #this variable will keep track of how many times a query has failed


#start selenium
print("Getting Firefox profile")
profile = FirefoxProfile("/Users/William/Library/Application Support/Firefox/Profiles/u27s2prt.default")
print("Setting driver...")
driver = webdriver.Firefox(profile)

# driver.set_page_load_timeout(180) #timeout after three minutes  #for some reason this stopped working for me in latest version??




def read_queries():
	global failures
	#get queries from txt
	with open('query.txt') as f:
		each_query = f.readlines()
	each_query = [x.strip() for x in each_query]

	querynum = 1 #keep track of number of (main)
	for query in each_query: #each line in the .txt is a new query. cycle through them all

		if query in done:
			print("Already did query: \"%s\" -- Moving on" % query)
			pass #skip already completed queries
		else:

			try:

				#get keyword, start and end date for each query
				s = query.split(';') 
				keyword = s[0] 
				start = s[1]
				end = s[2]

				if failures > 10:
					print("Too many failures. Probably API block. Breaking to resume later")
					#the script will exit. it's probably time to switch to a new weibo account, or verify by SMS
					break
				else:

					print("Session id: %s" % file[:-1])
					print("Beginning query %s out of %s" % (querynum,len(each_query)))

					#scrape each query
					(query_content, query_time) = scrape(keyword, start, end)

					#export to json
					export_json(file+str(querynum), keyword,query_content,query_time,query)

					querynum += 1

					done.append(query)

			except:
				print("Exception! Dumping pickle")


				#some kind of unknown error... print it out:
				print(traceback.format_exc()) #print the exception


				#Dump completed queries to resume later
				pickle.dump(done, open("query_done.pkl", "wb"))
				break

def scrape(keyword, start, end):
	global failures
	global driver
	#begin scraping. 
	#load the first page, check that it has results, and get number of total pages for query
	overflow = begin_scrape(keyword, start, end)


	#lists of all content for the whole query
	query_content = []
	query_time = []

	#break up into smaller queries if too big
	if overflow:
		print("Too many results for that query. Need to chop it into smaller ones by adjusting the date range")
		with open("overflows.txt","a") as f:
			f.write("keyword;start;end\n")
			f.write("%s;%s;%s\n" % (keyword, start, end))

		query_content.append("OVERFLOW"+keyword)
		query_time.append("OVERFLOW"+keyword)

		#automatically reduce date range (NOT IMPLEMENTED -- didn't have time to fully test)
		# chopped = chop_query(keyword, start, end)
		# for c in chopped:
		# 	#will stay in this loop until small enough
		# 	scrape(c)
	else:
		pass


	print("Starting to iterate through pages")
	for page in range(50):		
		delay=float(random.randint(800,1200))/100.0 #Sleep 8-12 seconds
		print("Waiting %s seconds" % delay)
		systime.sleep(delay)

		#read the page: load it in selenium & grab all content
		print("Reading page %s" % (str(page+1)))
		(page_content, page_time) = read_page(keyword, start, end, page)

		if len(page_content) > 0:
			print("Finished collecting content for that page.")
			for i in page_content:
				query_content.append(i)
			for i in page_time:
				query_time.append(i)
			if len(page_content) < 5:
				print("End of results. Breaking")
				# driver.close()
				break

		else:
			#not happy with this solution, but it helps keep from breaking due to rare page load errors
			print("Had a problem with page %s. Trying one more time" % (str(page+1)))
			print("Reading page %s" % (str(page+1)))
			(page_content, page_time) = read_page(keyword, start, end, page)

			if len(page_content) > 0:
				print("Finished collecting content for that page.")
				for i in page_content:
					query_content.append(i)
				for i in page_time:
					query_time.append(i)
				if len(page_content) < 5:
					print("End of results. Breaking")
					# driver.close()
					break

			else:
				print("Couldn't get page %s" % (str(page+1)))
				failures += 1

				with open("failures.txt","a") as f:
					f.write("keyword;start;end;page\n")
					f.write("%s;%s;%s;%s\n" % (keyword, start, end,page+1))	
								
				break


	#pass results back up to read_queries
	return (query_content, query_time)

# #reduce date range of query by cutting it in half (NOT IMPLEMENTED -- didn't have time to fully test)

# def chop_query(keyword, start, end):
#     print("Chopping")
#     chopped = []

#     end_end = end[-2:]
#     end_end = int(end_end)

#     half = int(0.5*(end_end+1))
#     start_half = start[:-2]+str(half+1)
#     end_half = end[:-2]+str(half)


#     top = (keyword, start_half, end)
#     bottom = (keyword, start, end_half)
#     chopped.append(top)
#     chopped.append(bottom)

    
#     print("New queries:")
#     print(chopped[0])
#     print(chopped[1])
#     print("Scraping each in turn")
#     # return (chopped)


#since chop_query() was not implemented, if you ever have more than 50 pages of results,
#you'll have to go into query.txt and reduce the date range manually
#the minimum date range you can search for is a single hour, i.e., '香港回归;2017-06-30-22;2017-06-30-23'
#if a single hour still has more than 50 pages of results, maybe try a more specific keyword



#load the first page, check that it has results, and return bool for whether or not query is too large
def begin_scrape(keyword,start,end,page=1):
	print("Beginning a new scrape for query: \"%s\"" % keyword)
	print("Date Range: %s - %s" % (start,end))	

	global driver

	URL_keyword = urllib.quote(urllib.quote(keyword)) #this is a formatted version of the keyword for URL input



	url = base_url + URL_keyword + "&typeall=1&haslink=1&timescope=custom:" + start + ":" + end + "&page=" + str(page)

	#load_url returns True when the page is loaded
	print("Loading URL: %s" % url)
	loaded = load_url(url)
	print("Waiting a moment to make sure first page is loaded")
	systime.sleep(10) #give it some extra time to load... sometimes it needs this. Adjust if necessary
	print("Beginning scrape")

	if loaded:
		print("Getting source")
		page_source = driver.page_source
		print("Parsing...")
		soup = BeautifulSoup(page_source, "html.parser")

		#see if there's a div class announcing no results for the page; returns bool
		has_results = check_results(soup)

		if has_results:
			overflow = check_overflow(soup)
			return overflow #the function ends here: passing overflow bool back up to scrape()

		else:
			print("Couldn't find any results on this page. Ending here.")
			pass

	else:
		print("Could not load first page.")
		pass
			
#catches timeouts & makes 10 attempts; returns True when successfully loaded
def load_url(url):
	global driver

	attempts = 0 #keep track of number of attempts
	while attempts < 10:
		try:
			print("Trying to load page...")
			driver.get(url)
			print("Success!")
			return True

		#try again if timeout
		except selenium.common.exceptions.TimeoutException:
			print("Timeout. Waiting 20 seconds")
			systime.sleep(20)
			attempts += 1
			pass

		# except KeyboardInterrupt:
		# 	print("Cancelled")
		# 	return False


		# except:
		# 	print("Unknown error.")
		# 	attempts += 1
		# 	return False


	print("Breaking after 10 failed attempts")
	return False

#see if there's a div class announcing no results for the page; returns bool
def check_results(soup):
	global driver
	noresult = soup.findAll("div", {"class" : "search_noresult"})

	if len(noresult) > 0:
		print("No results on this page.")
		return False
	else:
		print("Found some results.")
		return True

#this parses the soup for things that look like page number tags & returns the largest one
def check_overflow(soup):

	print("Looking for page count...")


	page_regx = re.compile(">第\d+页<")
	page_regx_result = page_regx.findall(str(soup))
	page_regx_result = [i.decode("utf-8") for i in page_regx_result]

	page_regx_result = [i[2:-2] for i in page_regx_result] #remove surrounding chars

	last = 1
	for i in page_regx_result:
		try:
			if int(i) > last:
				last = int(i)
			else:
				pass

		except:
			#if there's an error, safer just to assume we have over 50 pages for now
			last = 51

	print("Detected last page: %s" % last)

	if last == 50:
		return True
	else:
		return False

#returns a tuple: (page_content, page_time) where both items are lists
def read_page(keyword,start,end,page):
	global driver #continue with current selenium driver

	#collect all content for this page only
	page_content = []
	page_time = []

	URL_keyword = urllib.quote(urllib.quote(keyword)) #this is a formatted version of the keyword for URL input


	#my project required only posts containing a link, so that's filtered out in the URL.
	#if you want all posts regardless of whether or not they contain a link, remove '&haslink=1' from the string below.
	url = base_url + URL_keyword + "&typeall=1&haslink=1&timescope=custom:" + start + ":" + end + "&page=" + str(page + 1)

	print("Loading URL: %s" % url)
	loaded = load_url(url) #load page & only continue when successful

	if loaded:

		print("Getting source")
		page_source = driver.page_source
		print("Parsing...")
		soup = BeautifulSoup(page_source, "html.parser")

		#make sure there are results on the page
		has_results = check_results(soup)

		end_results = False

		if has_results == False:
			end_results = True
			print("Found a div class suggesting this is an empty page. Trying to get results anyway")

		else:
			pass
		#get all the content
		content = soup.findAll("div", { "action-type" : "feed_list_item" })
		time = soup.findAll("a", { "class" : "W_textb" })
		
		for each in content:
			page_content.append(each) #.get_text().encode('utf-8')
		print("Found %s posts" % len(page_content))

		timenum = 0
		for each in time:
			each = each.get_text()
			each = each.encode('utf-8')
			time = ""

			timenum += 1

			if "月" in each:
				time = str(datetime.datetime.now().year) + "-" + each[0:each.index("月")] + "-" + each[(each.index("月") + 3):each.index("日")]
			else:
				try:
					time = each[0:each.index(" ")]
				except:
					time = ("UNKNOWN_TIME_%s" % timenum)
					print("Unknown time for %s" % timenum)
			page_time.append(time)
		print("Assigning date for %s posts" % timenum)

		if end_results:
			if len(page_content) == 5:
				print("Looks like that was really the end. Skipping these 5")
				return(["END"],["END"])
			else:
				print("Number of results !=5. Saving just in case")
				return (page_content, page_time) #pass it back up to scrape()

		else:

			return (page_content, page_time) #pass it back up to scrape()


	else:
		print("Couldn't load this page.")
		return (page_content, page_time) #returning empty lists

#export json object containing full HTML for each post in the query + some metadata
def export_json(filename,keyword,content,time,query):

	if not os.path.exists('./output'):
		os.makedirs('./output')



	with open('./output/' + filename + '.json', 'w') as f:

	    allposts=[]
	    print("Found %s posts. Dumping to JSON" % len(content))
	    for i in range(len(content)):
	    	vals={"query":query,"postid":i+1,"keyword":keyword,"content":str(content[i]).encode("utf-8"),"date":str(time[i])}
	    	allposts.append(vals)
	    json.dump(allposts,f)
	    print("Done")


print("Loading page for test query")
operational = load_url(base_url+"test")
if operational:
	print("Successfully loaded test query. Beginning")
	read_queries() #start the machine
else:
	print("Could not load test query. ")

