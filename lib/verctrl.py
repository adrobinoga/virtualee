import os
from datetime import datetime


#############################################################################
# Related to version control methods(cloud copy vs local copy)
class VControl:

    def __init__(self, sce, hmg):
        self.cloud_trees = []
        self.sce = sce
        self.hmg = hmg

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

    def estimate_size(self, dest):
        """
        Estimates total size of update.
        :param dest: Path to local copy of materials.
        :return: Int, amount of bytes.
        """
        self.sce.get_course_list()
        cloud_trees = []

        size = 0
        # inspect each course
        for c in self.sce.nameurl_courses:
            # parse cloud course materials
            cloud_trees.append(self.sce.gen_cloud_tree(c, self.sce.nameurl_courses[c]))
            # estimate download size for each course
            size += self.estimate_size_tree(dest, cloud_trees[-1])
        return size

    def estimate_size_tree(self, dest, cloud_node):
        """
        Estimates size of download for one course.
        :param dest: Path to local copy.
        :param cloud_node: Representation of materials on eie-virtual site for one course.
        :return: Int, size given in bytes.
        """
        current_path = os.path.join(dest, cloud_node.name)
        size = 0
        # checks if current directory exist
        if not os.path.exists(current_path):
            for f in cloud_node.files:
                size += self.sce.get_file_size(f.url)

        else:
            # files of current tree level
            for f in cloud_node.files:
                curr_file_path = os.path.join(current_path, f.name)

                # include size of files when they don't exist on local copy or differ in size
                if not os.path.isfile(curr_file_path):
                    size += self.sce.get_file_size(f.url)
                else:
                    cloud_file_size = self.sce.get_file_size(f.url)
                    local_file_size = int(os.stat(curr_file_path).st_size)
                    if cloud_file_size != local_file_size:
                        size += self.sce.get_file_size(f.url)

        # does the same for next level of subdirectories
        for node in cloud_node.dirs:
            size += self.estimate_size_tree(current_path, node)
        return size

    def add2hist(self, name, course_name, date):
        """
        Adds an entry to download history.
        :param name: name of file.
        :param date: Float, date of download, time since epoch.
        :param course_name: course name to which it belongs.
        :return: None.
        """
        self.hmg.add_entry(name=name, course_name=course_name, date=date)

#############################################################################


#############################################################################
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
#############################################################################


#############################################################################
# Represents a file(pdf, docx, jpg, png ...)
class File:

    def __init__(self, name, url, size, date):
        self.name = name
        self.url = url
        self.date = date
        self.size = size
#############################################################################
