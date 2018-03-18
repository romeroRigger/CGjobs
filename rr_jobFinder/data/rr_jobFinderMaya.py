#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
================================================================================
rr_jobFinder.py - Python Script
================================================================================
www.romerorigger.com
info@romerorigger.com
*** MODIFY THIS AT YOUR OWN RISK ***

DESCRIPTION:
    SEARCH OFFLINE THE INFORMATION RELATED WITH THOUSANDS OF JOB OFFERS
    PROVIDED BY CHRIS MAYNE AND THEIR COLLABORATORS.

NOTES:
   NEXT VERSION:
        - new ways to scrap information from the job servers

    LIMITATIONS:
        - Use as Maya script

USAGE:
    ScriptEditor, Python Tab:

    import rr_jobFinder
    reload(rr_jobFinder)


DATE: MAR/2018
RELEASE DATE: 18/03/14
MAYA: 201X
'''


# Importing libraries:
try:
    import json
    import logging
    import maya.cmds as mc
    import os
    import re
    import urllib2
    import webbrowser

    from functools import partial
except Exception as e:
    print "Error: importing python modules!!!\n",
    print e

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ui():
    ui_object = JobFinderClass()


# =============================================================================


class JobFinderClass(object):
    """ A class for searching keywords into a database """

    def __init__(self,
                 data_file_name='job_data.json',
                 folder_path='{}/data'.format(os.path.dirname(os.path.realpath(__file__))),
                 online_version_url='https://git.io/vA5kO',
                 online_data_file='https://git.io/vA5kc',
                 window_name='jobFinder',
                 window_title='rr :: CG Job Finder',
                 window_width=400,
                 window_height=150):

        self.local_file_path = '{}/{}'.format(folder_path, data_file_name)
        self.local_data = None
        self.online_version_url = online_version_url
        self.online_data_file = online_data_file
        self.window_name = window_name
        self.window_title = window_title
        self.window_width = window_width
        self.window_height = window_height
        self.widgets = {'JobTitle': '', 'Country': ''}
        self.data_find = dict()
        self.message_text = None

        self.__open_file__()
        self.__build__()

    # UI Creation
    def __build__(self):
        """Creates the UI """
        if mc.window(self.window_name, ex=True):
            mc.deleteUI(self.window_name)

        # Create the window and its contents
        self.window = mc.window(self.window_name,
                                t=self.window_title,
                                w=self.window_width,
                                h=self.window_height,
                                menuBar=True, s=False, mnb=False, mxb=False)
        # Menu
        mc.menu(label='Help', helpMenu=True)
        mc.menuItem('update_data', label='Update your local data base',
                    c=partial(self.online_version_checker))
        mc.menuItem('posting', label='Post a job',
                    c=partial(self.about_dialog, "posting"))
        mc.menuItem(divider=True)
        mc.menuItem(subMenu=True, label='about')
        mc.menuItem('me', label='@romerorigger',
                    c=partial(self.about_dialog, 'me'))
        mc.menuItem('Chris', label='Chris Mayne',
                    c=partial(self.about_dialog, 'Chris'))
        mc.menuItem('gSheet', label='Animation Industry Job Postings',
                    c=partial(self.about_dialog, 'gSheet'))

        # =====================================================================
        # UI-Forms, Buttons, Layouts
        # =====================================================================
        self.main_layout = mc.columnLayout('main_layout', w=self.window_width, rs=5)

        # Main buttons and option menu fields
        self.w = self.window_width / 2 - 10
        mc.separator(h=5)
        mc.rowLayout('buttonsLayout', nc=3, cw=[(1, self.w), (2, self.w)])

        # textFieldGrp used to find a job title
        mc.textFieldGrp('text_job', w=self.w, cw2=[self.w * 0.25, self.w * 0.7],
                        tx='Job Title', h=20, label='  What :', cal=(1, 'left'),
                        tcc=partial(self.get_job_text))

        # optionMenu for every Country
        mc.optionMenu('menu_country', w=self.w, h=20, label='Where :',
                      cc=partial(self.get_country_text))
        # Method called to populate the menu country list
        self.populate_country()

        # Column layout
        mc.setParent(self.main_layout)
        mc.columnLayout(w=self.window_width, cw=self.window_width, cat=('both', 10))

        # Button find jobs
        mc.button(label='Find Jobs', h=20, bgc=(0, 0.75, 1), c=partial(self.job_finder))
        mc.separator(h=7, st="none")

        mc.setParent(self.main_layout)
        mc.columnLayout(w=self.window_width, cw=self.window_width, cat=('both', 10))
        # TextScrollList used with the job list
        mc.textScrollList('job_list', sc=partial(self.single_click_select), ams=False, h=150)

        # Infojob scrollField
        mc.separator(h=10, st="none")
        mc.scrollField('info_field', editable=False, text="", wordWrap=True, h=150)

        # Contact button
        mc.separator(h=7, st="none")
        mc.button(label='Contact', h=25, bgc=(0, 1, 0.75), c=partial(self.popup_contact))
        mc.separator(h=5, st="none")

        # Show window
        mc.showWindow(self.window_name)

    # =====================================================================
    # Methods to populate the info into the UI
    # =====================================================================
    def __open_file__(self, *args):
        """Get the file from local folder """
        with open(self.local_file_path) as job_data:
            self.local_data = json.load(job_data)

    def populate_country(self, *args):
        """Gets the data about the countries from the database to the optionMenu"""
        self.country_list = [p['Country'] for p in self.local_data['jobs']]

        for country in sorted(set(self.country_list)):
            mc.menuItem(label=country)

    def populate_jobs(self, *args):
        self.scroll_idx = 0
        mc.textScrollList('job_list', e=True, ra=True)
        for each in self.data_find.values():
            self.scroll_idx += 1
            mc.textScrollList('job_list', e=True, a=each['JobTitle'], utg=self.scroll_idx)

    def job_finder(self, *args):
        self.data_find.clear()
        self.job_idx = 0
        for p in self.local_data['jobs']:
            if re.search(self.widgets['Country'], p['Country'], re.IGNORECASE) \
                    and re.search(self.widgets['JobTitle'], p['JobTitle'], re.IGNORECASE):
                self.job_idx += 1
                self.data_find[self.job_idx] = p
        self.populate_jobs()

    def get_job_text(self, item, *args):
        self.widgets['JobTitle'] = item

    def get_country_text(self, item, *args):
        self.widgets['Country'] = item

    def single_click_select(self, *args):
        scroll_sel = mc.textScrollList('job_list', q=True, sii=True)
        self.info_job = json.loads(json.dumps(self.data_find[scroll_sel[0]], indent=2))
        self.contact_info()

    def contact_info(self):
        self.message_text = u'Studio    :  {}\nJob Title :  {}\nDate      :  {}\nSoftware  :  {}\
                            \nCity      :  {}\nST/PR     :  {}\nContact   :  {}\n'\
                            .format(
            self.info_job['Studio'],
            self.info_job['JobTitle'],
            self.info_job['Date'],
            self.info_job['Software'],
            self.info_job['City'],
            self.info_job['PR/ST'],
            self.info_job['Contact'])

        mc.scrollField('info_field', e=1, cl=1)
        mc.scrollField('info_field', text=self.message_text, e=1)

    def popup_contact(self, *args):
        """ Check if the contact info is URL or mail"""
        if re.search(r'\w+@', self.info_job['Contact']):
            webbrowser.open('mailto:?to={}&subject={}&body= Studio : {}\n'
                            .format(self.info_job['Contact'],
                                    self.info_job['JobTitle'],
                                    self.info_job['Studio']), new=1)

        elif re.search(r'^https?://', self.info_job['Contact']):
            mc.showHelp(self.info_job['Contact'], absolute=True)

        else:
            logger.info('without contact info')

    def about_dialog(self, www, *args):
        """ About the people who contribute or inspire the tool"""
        if www == "me":
            mc.showHelp('http://romerorigger.com', absolute=True)
        elif www == 'Chris':
            mc.showHelp('https://vimeo.com/chrismayne', absolute=True)
        elif www == 'gSheet':
            mc.showHelp("http://bit.ly/animationIndustryJobPostings", absolute=True)
        elif www == 'posting':
            mc.showHelp('http://bit.ly/cgjobsposting', absolute=True)

    # Methods to help the file updating
    def online_version_checker(self, *args):
        """Get the version from the online version """
        request_url = urllib2.Request(self.online_version_url)
        opener_url = urllib2.build_opener()
        url_file = opener_url.open(request_url)
        read_json = json.loads(url_file.read())
        self.online_version_number = int(read_json['version'])
        self.offline_version_checker()

    def offline_version_checker(self, *args):
        """ Get the version from the local database"""
        offline_version_number = int(self.local_data["version"])
        logger.info(offline_version_number)
        if offline_version_number == self.online_version_number:
            self.dialog_message = 'Your data is up to date\nwith the version {}'\
                .format(self.online_version_number)
            self.update_dialog()
        else:
            self.dialog_message = 'New data version: {}\n\nPlease Download the update and\
                                \nreplace the file "job_data.json" in: \n        rr_jobFinder/data'\
                                .format(self.online_version_number)
            self.update_dialog()

    def update_dialog(self, *args):
        """ Dialog that shows the comparison between versions online and local"""
        result = mc.confirmDialog(title='',
                                  message=self.dialog_message,
                                  button=['Download', 'Close'],
                                  defaultButton='Close',
                                  cancelButton='Close',
                                  dismissString='Close')
        if result == 'Download':
            self.save_updated_file()
            logger.info("Your data file was updated, please re-open the job Finder tool").info()

    def save_updated_file(self, *args):
        """Download de updated file from internet and save to the data scripts folder"""
        filedata = urllib2.urlopen(self.online_data_file)
        data_to_write = filedata.read()
        with open(self.local_file_path, 'wb') as f:
            f.write(data_to_write)


# Launch
if __name__ == "__main__":
    ui()
