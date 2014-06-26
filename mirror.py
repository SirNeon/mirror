import logging
import optparse
from sys import exit, stderr
from time import sleep
import praw
from praw.errors import *
from requests.exceptions import HTTPError


class trdbot(object):


    def __init__(self):
        """
        Initialize the bot with some basic info.
        """

        self.userAgent = "/r/TrueRedditDrama xposting bot by /u/SirNeon"

        # add terminal output
        self.verbose = False

        # list of subreddits to crawl
        self.subredditList = set([
                    "dickgirls",
                ])


        # list of threads already done
        self.alreadyDone = set()

        # list of threads with the source linked
        self.alreadyCommented = set()

        # post to this subreddit
        self.post_to = "dyckgyrls"

        # scan no more than this number of threads
        self.scrapeLimit = 1000


    def add_msg(self, msg=None, newline=False):
        """
        Simple function to make terminal output optional. Feed
        it the message to print out. Can alsotell it to print a 
        newline if you want to.
        """

        if(self.verbose):
            if msg is not None:
                print msg

            if(newline):
                print '\n'


    def login(self, username, password):
        """
        Login to the bot's Reddit account. Give it the username
        and the password.
        """

        self.client = praw.Reddit(user_agent=self.userAgent)
        print "Logging in as {0}...".format(username)

        self.client.login(username, password)
        print "Login was successful."


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
            trdBot.login(username, password)
            break

        except (InvalidUser, InvalidUserPass, RateLimitExceeded, APIException) as e:
            trdBot.add_msg(e)
            logging.debug("Failed to login. " + str(e) + "\n\n")
            exit(1)

        except HTTPError, e:
            trdBot.add_msg(e)
            logging.debug(str(e) + "\n\n")

            if i == 2:
                print "Failed to login."
                exit(1)

            else:
                # wait a minute and try again
                trdBot.add_msg("Waiting to try again...")
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
                print "Verifying /r/{0}...".format(subreddit)

                try:
                    # make sure the subreddit is valid
                    testSubmission = trdBot.client.get_subreddit(subreddit).get_new(limit=1)
                    for submission in testSubmission:
                        "".join(submission.title)

                except (InvalidSubreddit, RedirectException) as e:
                    trdBot.add_msg(e)
                    logging.debug("Invalid subreddit. Removing from list." + str(e) + "\n\n")
                    trdBot.subredditList.remove(subreddit)
                    raise skipThis

                except HTTPError, e:
                    trdBot.add_msg(e)
                    logging.debug(str(subreddit) + ' ' + str(e) + "\n\n")

                    # private subreddits return a 403 error
                    if "403" in str(e):
                        print "/r/{0} is private. Removing from list...".format(subreddit)
                        subredditList.remove(subreddit)
                        continue

                    # banned subreddits return a 404 error
                    if "404" in str(e):
                        print "/r/{0} probably banned. Removing from list...".format(subreddit)
                        trdBot.subredditList.remove(subreddit)
                        continue

                    trdBot.add_msg("Waiting a minute to try again...")
                    sleep(60)
                    raise skipThis

                except (APIException, ClientException, Exception) as e:
                    trdBot.add_msg(e)
                    logging.debug(str(e) + "\n\n")

                    if str(e) == "timed out":
                        trdBot.add_msg("Waiting to try again...")
                        sleep(60)
                        continue

                    else:
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
    if len(trdBot.alreadyDone) >= 1000:
        print "Trimming the list of finished submissions..."
        
        for i, element in enumerate(trdBot.alreadyDone):
            if i < 900:
                trdBot.alreadyDone.remove(element)


def main():
    username = ""
    password = ""

    # optional commandline arguments and features
    parser = optparse.OptionParser("python trdbot.py [options]")
    parser.add_option("-p", "--postHere", dest="postHere", type="string", help="Set the subreddit to post the results to.")
    parser.add_option("-v", "--verbosity", dest="verbosity", type="string", help="Make the program more verbose with status updates and error printing. Off by default.")
    parser.add_option("-u", "--userCreds", dest="userCreds", type="string", help="Give the bot the username and password to an account. Separate them with commas.")
    (options, args) = parser.parse_args()

    if options.verbosity is not None:
        if options.verbosity.lower() == "on":
            trdBot.verbose = True

        elif options.verbosity.lower() == "off":
            trdBot.verbose = False

        else:
            print "Invalid argument for verbosity. Use either \"on\" or \"off\"."
            exit(1)

    if options.userCreds is not None:
        credentials = options.userCreds.split(',')
        username = credentials[0]
        password = credentials[1]

    login(username, password)

    # This requires the client attribute, which is created
    # in the login function
    if options.postHere is not None:
        checkSub = [options.postHere]

        check_subreddits(checkSub)

        if checkSub == []:
            print "Subreddit failed check. Can't post there."
            exit(1)

        else:
            trdBot.post_to = options.postHere

    check_subreddits(trdBot.subredditList)

    print "Building multireddit."

    multireddit = ""

    for subreddit in trdBot.subredditList:
        multireddit += "".join(subreddit + '+')

    print "Multireddit built."

    while True:
        check_list()

        try:
            print "Scanning for submissions..."
            submissions = trdBot.client.get_subreddit(multireddit).get_hot(limit=trdBot.scrapeLimit)

        except (APIException, ClientException, HTTPError, Exception) as e:
            trdBot.add_msg(e)
            logging.debug(str(e) + "\n\n")
            trdBot.add_msg("Waiting to try again...")
            sleep(60)
            continue

        for i, submission in enumerate(submissions):
            trdBot.add_msg("Scanning thread ({0} / {1})...".format(i + 1, trdBot.scrapeLimit))

            try:
                postID = str(submission.id)
                subreddit = str(submission.subreddit)

            except AttributeError:
                print "Failed to get submission ID. Skipping..."
                continue

            try:
                if postID not in trdBot.alreadyDone:
                    trdBot.add_msg("Getting content from submission...")
                    result = trdBot.get_content(submission)

                else:
                    # needed to ease strain on CPU
                    sleep(2)

            except HTTPError, e:
                trdBot.add_msg(e)
                logging.debug(str(e) + "\n\n")
                sleep(60)
                continue

            except (APIException, ClientException, Exception) as e:
                trdBot.add_msg(e)
                logging.debug(str(e) + "\n\n")

                if str(e) == "timed out":
                    trdBot.add_msg("Waiting to try again...")
                    sleep(60)
                        
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
                trdBot.add_msg(e)
                logging.debug(str(e) + "\n\n")
                continue

            # try to submit the post 3 times before skipping
            for i in range(0, 3):
                try:
                    if postID not in trdBot.alreadyDone:
                        print "Submitting post..."
                        
                        content = content.replace("www.np.reddit.com", "np.reddit.com")

                        if(submission.is_self):
                            post = trdBot.submit_selfpost(title, content)

                        else:
                            post = trdBot.submit_url(title, content)

                        trdBot.alreadyDone.add(postID)

                    else:
                        # needed to ease strain on CPU
                        sleep(2)

                except HTTPError, e:
                    trdBot.add_msg(e)
                    logging.debug(str(e) + "\n\n")
                    sleep(60)
                    continue

                except (APIException, ClientException, Exception) as e:
                    trdBot.add_msg(e)
                    logging.debug(str(e) + "\n\n")

                    if str(e) == "`that link has already been submitted` on field `url`":
                        trdBot.alreadyDone.add(postID)
                        break

                    if str(e) == "timed out":
                        trdBot.add_msg("Waiting to try again...")
                        sleep(60)
                    
                    continue


if __name__ == "__main__":
    trdBot = trdbot()

    # set this to False to turn off error logging
    # doing so is not recommended
    errorLogging = True

    if(errorLogging):
        logging.basicConfig(
            filename="trdbot_logerr.log", filemode='a', 
            format="%(asctime)s\nIn %(filename)s "
            "(%(funcName)s:%(lineno)s): %(message)s", 
            datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG, 
            stream=stderr
            )

    main()
