import os
from datetime import datetime
import lib.histdocs as histdocs


# Related to version control methods(cloud copy vs local copy)
class VControl:

    def __init__(self, sce):
        self.cloud_trees = []
        self.sce = sce

    def gen_local_tree(self, rootdir):
        """
        Generates a Node object that represents the current contents of the local copy of a course materials.
        :param rootdir: path to local copy of course materials.
        :return: Node object with the current contents of the local copy.
        """
        parent_node = Node(os.path.split(rootdir)[1], "")
        self.get_local_docs(rootdir, parent_node)
        return parent_node

    def get_local_docs(self, rdir, node):
        """
        Parses the contents of the local copy and adds that info to a Node object.
        :param rdir: current directory level to parse.
        :param node: parent node to which subnodes and files are added.
        :return: None.
        """
        for elem in os.listdir(rdir):
                elem_path = os.path.join(rdir, elem)
                # adds all the files to the node, including time size info
                if os.path.isfile(elem_path):
                    stat_file = os.stat(elem_path)
                    itemdate = datetime.fromtimestamp(stat_file.st_mtime).strftime('%Y/%m/%d')
                    itemsize = str(round(stat_file.st_size/1024., 2))
                    node.add_file(File(elem, "", itemsize, itemdate))
                # adds all the folders, uses recursion to process folder leves
                else:
                    node.add_node(Node(elem, ""))
                    self.get_local_docs(elem_path, node.dirs[-1])

    def update_all(self, dest):
        """
        Updates local copy of all courses.
        :param dest: path to local copy.
        :return: None.
        """
        self.sce.get_course_list()
        # update each course
        for c in self.sce.nameurl_courses:
            # parse cloud course materials
            self.cloud_trees.append(self.sce.gen_cloud_tree(c, self.sce.nameurl_courses[c]))
            # update local copy of one course
            self.update_local_docs(dest, self.cloud_trees[-1], c)
        print "Update done"

    def update_local_docs(self, dest, cloud_node, course_name):
        """
        Updates local copy of course materials.
        :param course_name: coures name.
        :param dest: parent directory path.
        :param cloud_node: Node object, made with found materials in eie-virtual site.
        :return: None.
        """
        current_path = os.path.join(dest, cloud_node.name)
        # checks if current directory exist
        if not os.path.exists(current_path):
            os.makedirs(current_path)
            # then downloads all materials
            for f in cloud_node.files:
                self.sce.download_file(f.url, os.path.join(current_path, f.name))
                self.add2hist(f.name, "", course_name)
        else:
            # downloads materials in case don't exist in current copy
            for f in cloud_node.files:
                curr_file_path = os.path.join(current_path, f.name)
                if not os.path.isfile(curr_file_path):
                    print "Updating ", f.name
                    self.sce.download_file(f.url, curr_file_path)
                    self.add2hist(f.name, "", course_name)

        # does the same for next level of subdirectories
        for node in cloud_node.dirs:
            self.update_local_docs(current_path, node, course_name)

    def add2hist(self, name, date, course_name):
        """
        Adds an entry to download history.
        :param name: name of file.
        :param date: date of download.
        :param course_name: course name to which it belongs.
        :return: None.
        """
        histdocs.add_entry('download_date', name=name, date=date, course_name=course_name)

    def get_all(self, dest):
        """
        Download all course materials from all courses.
        :param dest: path of local copy.
        :return: None
        """
        # parse info of cloud
        for c in self.sce.nameurl_courses:
            self.cloud_trees.append(self.sce.gen_cloud_tree(c, self.sce.nameurl_courses[c]))
        # download all from cloud
        for t in self.cloud_trees:
            self.download_tree(t, dest)

    def download_tree(self, node, dest):
        """
        Downloads all contents, level by level.
        :param node: Node object with info of cloud materials.
        :param dest: parent directory of where to save materials.
        :return: None.
        """
        curr_path = os.path.join(dest, node.name)  # forms current path
        # if doesn't exist, it must be created
        if not os.path.exists(curr_path):
            os.makedirs(curr_path)

        # download all files
        for f in node.files:
            self.sce.download_file(f.url, os.path.join(curr_path, f.name))

        # step down one folder level (recursion)
        for d in node.dirs:
            self.download_tree(d, curr_path)


# Represents a directory and its contents, folders as Node Objects and files as File objects
class Node:
    def __init__(self, name, itemurl):
        self.name = name
        self.url = itemurl
        self.dirs = []
        self.files = []

    def add_file(self, f):
        """
        Adds one file to the current node.
        :param f: File object that may represent documents, images, scripts etc.
        :return: None.
        """
        self.files.append(f)

    def add_node(self, n):
        """
        Adds one node to the current node.
        :param n: Node that represents a directory.
        :return: None.
        """
        self.dirs.append(n)

    def show(self, ntabs=1):
        """
        Creates a string with the current nodes and files of a parent node.
        :param ntabs: number of indent tabs, integer.
        :return: String that shows the contents of the node in a tree-like structure.
        """
        str_files = (ntabs-1)*"\t"+"|"+self.name+" : \n"
        for f in self.files:
            str_files += ntabs*"\t"+"*"+f.name+", size="+f.size+", date="+f.date+"\n"
        for d in self.dirs:
            str_files += d.show(ntabs+1)
        return str_files


# Represents a file(pdf, docx, jpg, png ...)
class File:

    def __init__(self, name, url, size, date):
        self.name = name
        self.url = url
        self.date = date
        self.size = size
