import logging
import optparse
import os
from socket import timeout
from sys import exit, stderr
from time import sleep
import praw
from praw.errors import *
from requests.exceptions import HTTPError
from simpleconfigparser import simpleconfigparser


class mirrorbot(object):


    def __init__(self):
        """
        Initialize the bot with some basic info.
        """

        if(os.path.isfile("settings.cfg") == False):
            print("Could not find settings.cfg. Exiting...")
            exit(1)

        self.config = simpleconfigparser()

        self.config.read("settings.cfg")

        self.userAgent = "xposting bot by /u/SirNeon"

        # add terminal output
        self.verbose = self.config.main.getboolean("verbose")

        # list of subreddits to crawl
        self.subredditList = set(self.config.main.subreddits.split(','))

        # enable errorLogging
        self.errorLogging = self.config.logging.getboolean("errorLogging")

        # list of threads already done
        self.alreadyDone = set()

        # post to this subreddit
        self.post_to = self.config.main.post_to

        # scan no more than this number of threads
        self.scrapeLimit = int(self.config.main.scrapeLimit)


    def add_msg(self, msg=None, newline=False):
        """
        Simple function to make terminal output optional. Feed
        it the message to print out. Can also tell it to print a 
        newline if you want to.
        """

        if(self.verbose):
            if msg is not None:
                print(msg)

            if(newline):
                print('\n')


    def login(self, username, password):
        """
        Login to the bot's Reddit account. Give it the username
        and the password.
        """

        self.client = praw.Reddit(user_agent=self.userAgent)
        print("Logging in as {0}...".format(username))

        self.client.login(username, password)
        print("Login was successful.")


    def get_content(self, submission):
        """
        Gets data from the desired submission. Feed it the 
        submission. It returns a tuple containing the title,
        the post content, and the link to the source.
        """

        try:
            subName = str(submission.subreddit)
            postID = str(submission.id)
            title = str(submission.title)
            permalink = str(submission.permalink.replace("www.reddit.com", "np.reddit.com"))

        except AttributeError:
            raise Exception("Couldn't get submission attribute.")

        if 1 == 1:
            if(submission.is_self):
                try:
                    postBody = str(submission.selftext)

                except AttributeError:
                    raise Exception("Couldn't get submission text. Skipping...")

                text = postBody.replace("www.reddit.com", "np.reddit.com")

                return (title, text, permalink)

            else:
                url = str(submission.url.replace("www.reddit.com", "np.reddit.com"))

            return (title, url, permalink)

        else:
            self.add_msg("This shouldn't happen.")
            sleep(2)
            return None


    def submit_url(self, title, url):
        """
        Submits a link post to Reddit. Feed it the post title 
        and the url. It returns the submission object.
        """

        mySubreddit = self.client.get_subreddit(self.post_to)

        return mySubreddit.submit(title=title, url=url)


    def submit_selfpost(self, title, text):
        """
        Submits the self post to reddit. Feed it the post 
        title and post content. It returns the submission object.
        """

        mySubreddit = self.client.get_subreddit(self.post_to)

        return mySubreddit.submit(title=title, text=text)


class skipThis(Exception):
    pass


def login(username, password):
    """
    Tell the bot to login to Reddit. Feed it the username and
    password for the bot's Reddit account.
    """

    for i in range(0, 3):
        try:
            mirrorBot.login(username, password)
            break

        except (InvalidUser, InvalidUserPass, RateLimitExceeded, APIException) as e:
            mirrorBot.add_msg(e)
            logging.error("Failed to login. " + str(e) + "\n\n")
            exit(1)

        except HTTPError, e:
            mirrorBot.add_msg(e)
            logging.error(str(e) + "\n\n")

            if i == 2:
                print("Failed to login.")
                exit(1)

            else:
                # wait a minute and try again
                mirrorBot.add_msg("Waiting to try again...")
                sleep(60)
                continue


def check_subreddits(subredditList):
    """
    Checks on the listed subreddits to make sure that they are 
    valid subreddits and that there's no typos and whatnot. This 
    function removes the bad subreddits from the list so the bot 
    can carry on with its task. Feed it the list of subreddits.
    """

    for i in range(0, 3):
        try:
            for subreddit in subredditList:
                print("Verifying /r/{0}...".format(subreddit))

                try:
                    # make sure the subreddit is valid
                    testSubmission = mirrorBot.client.get_subreddit(subreddit).get_new(limit=1)
                    for submission in testSubmission:
                        "".join(submission.title)

                except (InvalidSubreddit, RedirectException) as e:
                    mirrorBot.add_msg(e)
                    logging.error("Invalid subreddit. Removing from list." + str(e) + "\n\n")
                    mirrorBot.subredditList.remove(subreddit)
                    raise skipThis

                except (HTTPError, timeout) as e:
                    mirrorBot.add_msg(e)
                    logging.error(str(subreddit) + ' ' + str(e) + "\n\n")

                    # private subreddits return a 403 error
                    if "403" in str(e):
                        print("/r/{0} is private. Removing from list...".format(subreddit))
                        subredditList.remove(subreddit)
                        continue

                    # banned subreddits return a 404 error
                    if "404" in str(e):
                        print("/r/{0} probably banned. Removing from list...".format(subreddit))
                        mirrorBot.subredditList.remove(subreddit)
                        continue

                    mirrorBot.add_msg("Waiting a minute to try again...")
                    sleep(60)
                    raise skipThis

                except (APIException, ClientException, Exception) as e:
                    mirrorBot.add_msg(e)
                    logging.error(str(e) + "\n\n")
                    raise skipThis

            break

        except skipThis:
            if i == 2:
                print "Couldn't verify the validity of the listed subreddits. Quitting..."
                exit(1)

            else:
                continue

    print "Subreddit verification completed."


def check_list():
    """
    This bot is intended to run 24/7. The list of finished 
    submissions could get quite large depending the activity 
    of the subreddits that it scans. This function trims the 
    list every so often so that it doesn't eat too much resources.
    """
    # keep the list from getting too big
    if len(mirrorBot.alreadyDone) >= 1000:
        print "Trimming the list of finished submissions..."
        
        for i, element in enumerate(mirrorBot.alreadyDone):
            if i < 900:
                mirrorBot.alreadyDone.remove(element)


def main():
    username = mirrorBot.config.login.username
    password = mirrorBot.config.login.password

    login(username, password)

    check_subreddits(mirrorBot.subredditList)

    print "Building multireddit."

    multireddit = ""

    for subreddit in mirrorBot.subredditList:
        multireddit += "".join(subreddit + '+')

    print "Multireddit built."

    while True:
        check_list()

        try:
            print "Scanning for submissions..."
            submissions = mirrorBot.client.get_subreddit(multireddit).get_hot(limit=mirrorBot.scrapeLimit)

        except (APIException, ClientException, HTTPError, Exception) as e:
            mirrorBot.add_msg(e)
            logging.error(str(e) + "\n\n")
            mirrorBot.add_msg("Waiting to try again...")
            sleep(60)
            continue

        for i, submission in enumerate(submissions):
            mirrorBot.add_msg("Scanning thread ({0} / {1})...".format(i + 1, mirrorBot.scrapeLimit))

            try:
                postID = str(submission.id)
                subreddit = str(submission.subreddit)

            except AttributeError:
                print "Failed to get submission ID. Skipping..."
                continue

            try:
                if postID not in mirrorBot.alreadyDone:
                    mirrorBot.add_msg("Getting content from submission...")
                    result = mirrorBot.get_content(submission)

                else:
                    # needed to ease strain on CPU
                    sleep(2)

            except UnicodeEncodeError:
                if postID not in mirrorBot.alreadyDone:
                    mirrorBot.alreadyDone.add(postID)
                
                continue

            except (HTTPError, timeout) as e:
                mirrorBot.add_msg(e)
                logging.error(str(e) + "\n\n")
                sleep(60)
                continue

            except (APIException, ClientException, Exception) as e:
                mirrorBot.add_msg(e)
                logging.error(str(e) + "\n\n")
                continue

            try:
                if result != None:
                    # concatenate elements from the 
                    # tuple to strings for submission
                    title = "".join(str(result[0]))
                    content = "".join(str(result[1]))
                    permalink = "".join(str(result[2]))

                else:
                    continue

            except Exception, e:
                mirrorBot.add_msg(e)
                logging.error(str(e) + "\n\n")
                continue

            # try to submit the post 3 times before skipping
            for i in range(0, 3):
                try:
                    if postID not in mirrorBot.alreadyDone:
                        print "Submitting post..."
                        
                        content = content.replace("www.np.reddit.com", "np.reddit.com")

                        if(submission.is_self):
                            post = mirrorBot.submit_selfpost(title, content)

                        else:
                            post = mirrorBot.submit_url(title, content)

                        mirrorBot.alreadyDone.add(postID)

                    else:
                        # needed to ease strain on CPU
                        sleep(2)

                except (HTTPError, timeout) as e:
                    mirrorBot.add_msg(e)
                    logging.error(str(e) + "\n\n")
                    sleep(60)
                    continue

                except (APIException, ClientException, Exception) as e:
                    mirrorBot.add_msg(e)
                    logging.error(str(e) + "\n\n")

                    if str(e) == "`that link has already been submitted` on field `url`":
                        mirrorBot.alreadyDone.add(postID)
                        break
                    
                    continue


if __name__ == "__main__":
    mirrorBot = mirrorbot()

    if(mirrorBot.errorLogging):
        logging.basicConfig(
            filename="mirrorbot_logerr.log", filemode='a', 
            format="%(asctime)s\nIn %(filename)s "
            "(%(funcName)s:%(lineno)s): %(message)s", 
            datefmt="%Y-%m-%d %H:%M:%S", level=logging.ERROR, 
            stream=stderr
            )

    main()
