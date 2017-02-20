import sqlite3

table_def = '(filename text, course text, date real)'


# Manages history database
class HistMg:
    def __init__(self, hist_record_path):
        self.hist_record_path = hist_record_path
        conn_hist = sqlite3.connect(self.hist_record_path)
        cursor_hist = conn_hist.cursor()

        # create table
        sql_cmd = """
        CREATE TABLE IF NOT EXISTS recent_files {0}
        """.format(table_def)

        cursor_hist.execute(sql_cmd)
        conn_hist.commit()
        cursor_hist.close()
        conn_hist.close()

    def add_entry(self, name, course_name, date):
        """
        Adds a new file-download entry to database.
        :param name: Filename.
        :param course_name: Course name.
        :param date: Float, time since epoch.
        :return: None
        """
        conn_hist = sqlite3.connect(self.hist_record_path)
        cursor_hist = conn_hist.cursor()

        # adds entry
        new_recent = [(name, course_name, date)]
        cursor_hist.executemany("INSERT INTO recent_files VALUES (?,?,?)", new_recent)
        conn_hist.commit()

        cursor_hist.close()
        conn_hist.close()

    def get_entries(self, course_name=None):
        """
        Gets all file entries from one course or all entries if no course is specified.
        :param course_name: course name.
        :return: List of dictionaries, where every dictionary has the keys (filename, course, date).
        """
        conn_hist = sqlite3.connect(self.hist_record_path)
        cursor_hist = conn_hist.cursor()

        if course_name:
            # get all of one course
            sql_cmd = u"SELECT * FROM recent_files WHERE course='{0}'".format(course_name)

        else:
            # get all
            sql_cmd = "SELECT * FROM recent_files"

        cursor_hist.execute(sql_cmd)

        # gen list of dicts
        fields_names = [description[0] for description in cursor_hist.description]
        items = []
        for i in cursor_hist.fetchall():
            items += [dict(zip(fields_names, i))]

        cursor_hist.close()
        conn_hist.close()
        return items

    def clear_hist(self, course_name=None):
        """
        Erases file-download entries of one course or all entries if no course is specified.
        :param course_name: course name.
        :return: None
        """
        conn_hist = sqlite3.connect(self.hist_record_path)
        cursor_hist = conn_hist.cursor()

        if course_name:
            # deletes all items from one course
            sql_cmd = u"""
            DELETE FROM recent_files
            WHERE course='{0}'
            """.format(course_name)

        else:
            # delete all
            sql_cmd = """
                        DELETE FROM recent_files
                        """

        cursor_hist.execute(sql_cmd)
        conn_hist.commit()

        cursor_hist.close()
        conn_hist.close()
