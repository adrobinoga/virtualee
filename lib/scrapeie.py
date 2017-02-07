import os
import requests
from bs4 import BeautifulSoup
from shutil import copyfileobj
import verctrl

urleie = "http://cursos.eie.ucr.ac.cr/"
loginurl = "https://cursos.eie.ucr.ac.cr/claroline/auth/login.php"


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
            # process each item according to item type(icon), don't you like this? me neither
            if "folder" in srcicon:
                # if folder then add Node
                node.add_node(verctrl.Node(name, itemtailurl))
                self.get_material_list(node.dirs[-1].url, node.dirs[-1])
            elif "image" in srcicon:
                itemtailurl = self.get_image_url(
                    itemtailurl)  # cannot process as a regular file, need this intermediate step
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
        print "Downloading ", dest.split(os.sep)[-1]
        tries = 0
        while tries < 3:
            try:
                tries += 1
                r = self.s.get(urleie + tailurldoc, stream=True)
            except requests.ConnectionError as err:
                print err
                if tries < 3:
                    print "trying to reconnect"
                    self.log_in()
                else:
                    raise requests.ConnectionError

        with open(dest, "wb") as dfile:
            copyfileobj(r.raw, dfile)
