import os
import requests
from bs4 import BeautifulSoup
import verctrl

urleie = "http://cursos.eie.ucr.ac.cr/"
loginurl = "https://cursos.eie.ucr.ac.cr/claroline/auth/login.php"


#############################################################################
# Related to web-scrapping of eie-virtual site
class ScrapEie:
    def __init__(self):
        self.name_courses = []
        self.urls_courses = []
        self.s = requests.Session()
        self.nameurl_courses = None
        self.username = ""
        self.password = ""

    def set_cred(self, username, password):
        """
        Stores user credentials for posterior sign-in.
        :param username:
        :param password:
        :return: None.
        """
        self.username = username
        self.password = password

    def log_in(self):
        """
        Logins to eie-virtual site, using previously stored credentials.
        :return: full name of user, empty String if no success.
        """
        # tries to log in
        data = {'login': self.username, 'password': self.password}
        self.s.post(urleie, data)

        # checks if the log in was successful
        r = self.s.get(urleie)
        soup = BeautifulSoup(r.content, "lxml")
        if soup.find_all("li", "userName"):
            fullname = soup.find_all("li", "userName")[0].string.strip()
            return fullname
        else:
            return ""

    def get_course_list(self):
        """
        Gets the all the courses of the current logged user, stores the result in a dict with the form
        {'course name': <complete url to the course homepage>}.
        :return: None.
        """
        # clear old list
        self.name_courses = []
        self.urls_courses = []

        # gets course list
        dash_eie = self.s.get(urleie)
        soupeie = BeautifulSoup(dash_eie.content, "lxml")
        courselist_dl = soupeie.find_all("dl", "courseList")

        # process each course
        for c in courselist_dl[0].find_all("dt"):
            lc = c.find_all("a")
            self.urls_courses += [urleie + lc[0].get("href")]
            self.name_courses += [lc[0].string]
            self.nameurl_courses = dict(zip(self.name_courses, self.urls_courses))

    def get_docs_url(self, urlc_homepage):
        """
        Gets the url for course documents given the link of a course.
        :param urlc_homepage: url of the course homepage.
        :return: url to course documents.
        """
        course_hp = self.s.get(urlc_homepage)
        soupc = BeautifulSoup(course_hp.content, "lxml")
        course_a = soupc.find_all("a", id="CLDOC")
        return course_a[0].get("href")

    def get_material_list(self, tail_urldoc, node):
        """
        Analyzes a level of course materials, stores the info (files folder with urls and so) in a Node object.
        :param tail_urldoc: last part of a course url.
        :param node: Node object to store the results.
        :return: None
        """
        # downloads page
        soupdoc = BeautifulSoup(self.s.get(urleie + tail_urldoc).content, "lxml")
        docitems = soupdoc.tbody.find_all("tr")

        # process course documents items(pdfs, images, scripts, folders etc)
        for item in docitems:
            itd = item.find_all("td")
            # ignore everything but items
            if not itd[0].find_all("a", {"class": "item"}):
                continue

            name = itd[0].a.text[1:]  # get the name of the item
            srcicon = itd[0].img.get("src")  # gets the path of the used icon(we may infer the item type from this)
            itemtailurl = itd[0].a.get("href")  # last part of the url to the contents of the folder or download url

            itemsize = itd[1].text
            # itemdate = itd[2].text

            # process each item according to item type(icon)
            if "folder" in srcicon:
                # if folder then add Node
                node.add_node(verctrl.Node(name, itemtailurl))
                self.get_material_list(node.dirs[-1].url, node.dirs[-1])
            elif "image" in srcicon:
                # cannot process as a regular file, need this intermediate step
                itemtailurl = self.get_image_url(itemtailurl)
                node.add_file(verctrl.File(name, itemtailurl, itemsize, ""))
            else:
                # everything else docx, pdfs, scripts ...
                node.add_file(verctrl.File(name, itemtailurl, itemsize, ""))

    def get_image_url(self, img_url):
        """
        Gets the download url of an image item.
        :param img_url: url of image item.
        :return: download image url.
        """
        soupim = BeautifulSoup(self.s.get(urleie + img_url).content, "lxml")
        return soupim.body.find_all("img", {"id": "mainImage"})[0].get("src")

    def gen_cloud_tree(self, namec, urlhp):
        """
        Parses the contents of a course contents and generates a Node object to store the results.
        :param namec: course name.
        :param urlhp: complete url to course homepage.
        :return: Node object containing all info of cloud course materials.
        """
        # get course materials url
        tail_urldocs = self.get_docs_url(urlhp)
        # parse course materials contents and store the result in a Node object
        parent_node = verctrl.Node(namec, "")
        self.get_material_list(tail_urldocs, parent_node)
        return parent_node

    def download_file(self, tailurldoc, dest):
        """
        Downloads a file.
        :param tailurldoc: last part of download url.
        :param dest: destination path, where to save the file.
        :return: None.
        """
        print "Downloading: ", dest.split(os.sep)[-1]
        tries = 0
        while tries < 3:
            try:
                tries += 1
                r = self.s.get(urleie + tailurldoc, stream=True)
            except requests.ConnectionError as err:
                print err
                if tries < 3:
                    print "Trying to reconnect"
                    self.log_in()
                else:
                    raise requests.ConnectionError
            else:
                if r.status_code == 200:
                    with open(dest, 'wb') as dfile:
                        for chunk in r:
                            dfile.write(chunk)
                else:
                    print "Couldn't download:", dest.split(os.sep)[-1]
                return

    def get_file_size(self, tailurldoc):
        """
        :param tailurldoc: last part of download url.
        :return: Int, size in bytes.
        """
        tries = 0
        while tries < 3:
            try:
                tries += 1
                r = self.s.head(urleie + tailurldoc)

            except requests.ConnectionError as err:
                print err
                if tries < 3:
                    print "Trying to reconnect"
                    self.log_in()
                else:
                    raise requests.ConnectionError
            else:
                return int(r.headers['Content-Length'])
#############################################################################


#############################################################################
# Methods to turn relative urls given on ads, into absolute urls
def get_absolute(root_url, url):
    """
    Receives a url and converts it to an absolute url using a given root url.
    :param root_url:
    :param url:
    :return: Absolute url.
    """
    if '//' in url[:url.find(">")]:
        return url
    else:
        return root_url + url


def link_refact(ann, root_url):
    """
    Finds relative paths on a given ad, and makes those absolute, using a given root url.
    :param ann: String, announcement to refactor.
    :param root_url:
    :return: String, announcement with absolute urls.
    """
    splited_ann = u'{0}'.format(ann).split("href=\"")

    refactored_ann = ""
    refactored_ann += splited_ann[0]
    for n in range(1, len(splited_ann)):
        splited_ann[n] = get_absolute(root_url, splited_ann[n])
        refactored_ann += u"href=\"{0}".format(splited_ann[n])

    return refactored_ann
#############################################################################


#############################################################################
# Methods for scraping news from eie main page
url_main_eie = "http://eie.ucr.ac.cr/"


def get_anns():
    """
    Gets all the recent news from eie.ucr.ac.cr.
    :return: Dictionary, where the keys are the announcement titles and values are the announcement contents.
    """
    s = requests.Session()

    # get raw news from site
    eieucr = s.get(url_main_eie)
    soupeieucr = BeautifulSoup(eieucr.content, "lxml")
    newsitems = soupeieucr.find_all("div", {"id": "news"})[0].find_all("div", {"class": "NewsSummary"})
    news = {}

    # process each ad
    for n in newsitems:
        # ad title
        ann_title = n.find_all("div", {"class": "NewsSummaryLink"})[0]
        # ad content
        ann_content = link_refact(n.find_all("div", {"class": "NewsSummarySummary"})[0], url_main_eie)
        # add notice to dict
        news.update({ann_title: ann_content})
    return news
#############################################################################


#############################################################################
url_empleo = "http://empleo.eie.ucr.ac.cr"
url_empleo_works = "http://empleo.eie.ucr.ac.cr/works"
url_empleo_sol = "http://empleo.eie.ucr.ac.cr/session"


# Scraps job ads from eie-empleo
class ScrapEmpleo:

    def __init__(self):
        self.s = requests.Session()
        self.get_job_anns()
        self.username = ""
        self.password = ""

    def set_creds(self, username, password):
        """
        Sets credentials.
        :param username:
        :param password:
        :return: None.
        """
        self.username = username
        self.password = password

    def log_in(self):
        """
        Log in to eie-empleo site, given a previously set credentials.
        :return:
        """
        r = self.s.get(url_empleo)
        soup = BeautifulSoup(r.content, "lxml")

        # get login form
        hidden_inputs = soup.find_all("input")
        form = {x.get("name"): x.get("value") for x in hidden_inputs}

        # tries to log in
        form['login'] = self.username
        form['password'] = self.password
        self.s.post(url_empleo_sol, form)

        # checks for login success
        r = self.s.get(url_empleo)
        empleo_html = BeautifulSoup(r.content, "lxml")
        if "Logeado como:" in empleo_html.text:
            return True
        else:
            print "Couldn't log in to " + url_empleo
            return False

    def get_job_anns(self):
        """
        Gets all the recent job ads.
        :return: List of strings, where each string is an add with html formatting.
        """
        r = self.s.get(url_empleo_works, timeout=5)
        empleo_html = BeautifulSoup(r.content, "lxml")
        newsitems = empleo_html.find_all("div", {"class": "title_notice"})

        anns = []
        for n in newsitems:
            anns += [link_refact(n.a, url_empleo)]
        return anns
#############################################################################
