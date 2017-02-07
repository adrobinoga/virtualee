import os
import json

"""
history structure:

{
criteria0:
        [ file_item0, file_item1 ... ]
criteria1:
        [ ... ]
}

file item:
{name : ____, course : ____, date : ____}
"""

conf_parent = os.path.join(os.environ['HOME'], ".virtualee")
hist_record_path = os.path.join(conf_parent, "history.json")

criteria_keys = ['download_date', 'lastm_date']
hist_record = {criteria_keys[0]: [], criteria_keys[1]: []}
entry_keys = ['name', 'course_name', 'date']


def setup_hist():
    """
    Creates history file if necessary.
    :return: None.
    """
    if not os.path.isfile(hist_record_path):
        with open(hist_record_path, 'w') as f:
            json.dump(hist_record, f)


def add_entry(criteria, name, date, course_name):
    """
    Adds one file entry to history file.
    :param criteria: criteria used for dates.
    :param name: file name.
    :param date: may be date of download or creation.
    :param course_name: course name to which current file belongs.
    :return: None.
    """
    e = Entry(name, course_name, date)

    with open(hist_record_path, 'r') as f:
        hrec = json.load(f)

    if criteria in hrec:
        hrec[criteria] += [e.get_entry()]

    with open(hist_record_path, 'w') as f:
        json.dump(hrec, f)


def get_entries(criteria=None, course_name=None):
    """
    Get list of file entries from history file.
    :param criteria: criteria for dates.
    :param course_name: course name.
    :return: list of file items from history file.
    """
    with open(hist_record_path, 'r') as f:
        hrec = json.load(f)

    if criteria:
        if course_name:
            # get all of one course
            course_entries = []
            for i in hrec[criteria]:
                if i['course_name'] == course_name:
                    course_entries += [i]
            return course_entries
        else:
            # get all of one criteria
            return hrec[criteria]
    else:
        # get all
        all_entries = []
        for k in criteria_keys:
            all_entries += (get_entries(k))
        return all_entries


def clear_hist(criteria=None, course_name=None):
    """
    Erases all the file items in the history file with a given criteria and course name.
    :param criteria: criteria for dates, may be download dates or modification dates.
    :param course_name: course name.
    :return: None.
    """
    with open(hist_record_path, 'r') as f:
        hrec = json.load(f)

    if criteria:
        if course_name:
            # deletes all items from one course
            n = 0
            while n < len(hrec[criteria]):
                if hrec[criteria][n]['course_name'] == course_name:
                    hrec[criteria].remove(hrec[criteria][n])
                else:
                    n += 1

        else:
            # delete one criteria
            while 0 != len(hrec[criteria]):
                hrec[criteria].remove(hrec[criteria][0])
    # delete all of one criteria
    None

    with open(hist_record_path, 'w') as f:
        json.dump(hrec, f)


# Represents one file download event
class Entry:

    def __init__(self, name, course_name, date):
        self.name = name
        self.course_name = course_name
        self.date = date

    def get_entry(self):
        """
        Gets all attributes of the entry as a dict.
        :return: dictionary with the form {'name': <file name>, 'course_name': <course name>, 'date': <date>}
        """
        return dict(zip(entry_keys, [self.name, self.course_name, self.date]))
