0. I recommend using Sublime Text or your IDE of choice to open up the script and read through it before running, so you can get an idea of what it does. I have generous comments and print statements so it should be pretty easy to follow along. Doing this first will make debugging easier—I can't guarantee it will work out of the box for you, since I've only run it on my own machine.

1. This script (scraperFork_v1.5.py) requires Python2.7 plus all the packages listed at the top of the .py file. Make sure these are all installed before continuing. 

1.a. Also make sure Firefox is installed, then navigate to /Users/<your username>/Library/Application Support/Firefox/Profiles/ and move the 'u27s2prt.default' directory inside. If you've already had Selenium working, this might not be necessary, but make sure the profile in the script matches the one on your machine.

1.b. I used a Mac and Firefox. If you're using a PC, or a browser other than Firefox with Selenium, you'll need to tailor these steps to your own setup. I can't help you there but it shouldn't be too hard with Google.

2. Open Firefox and log in to Weibo. Make sure you have cookies enabled and "下次自动登录" is ticked. Relaunch firefox and navigate to Weibo—you should still be logged in. This way when Selenium loads a Weibo page, it's doing so as a logged in user. Otherwise, your search results may be limited to a single page.

3. In Terminal, navigate to the directory where you put the script. Make sure geckodriver and a properly formatted query.txt are in that directory as well. (Use the example query.txt as a template. You'll need a keyword, a start date, and an end date. You can add as many lines as you want, but I recommend starting small to make sure it's working.)

4. Run this command: export PATH=.:$PATH

5. Run this command: python2.7 scraperFork_v1.5.py

6. Keep an eye on the terminal to follow along with its progress

7. Your results will be saved in the /output/ folder with a separate JSON object for each query. If I recall correctly, it contains the full HTML for each post, so you'll have to parse these with beautifulsoup to get what you want from it. I did this with separate scripts, which I plan to add in a separate repository soon.