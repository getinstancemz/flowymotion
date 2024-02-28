import requests
import email
import json 
import quopri
from bs4 import BeautifulSoup
#from datetime import datetime, timedelta
#from dateutil.parser import parse
import re

class MotionTask:
    def __init__(self, name, desc):
        self.name=name
        self.desc=desc
    def __repr__(self):
        return f"name: {self.name} / desc: {self.desc}"
    def __str__(self):
        return f"name: {self.name} / desc: {self.desc}"

class MotionTaskWriter:
    def __init__(self, conf, motiontasks):
        self.conf = conf 
        self.motiontasks = motiontasks
    def write_all(self):
        for task in self.motiontasks:
            self.write_task(task)

    def write_task(self, task):
        payload = {
            "workspaceId": conf.workspaceId,
            "name": task.name,
            "description": task.desc
        }
        response = requests.post("https://api.usemotion.com/v1/tasks",
            json=payload,
            headers={
                'X-API-Key': conf.apikey,
                'Content-Type': 'application/json'
            })
        response.raise_for_status()
        print(response)
        print(response.content)

class WorkflowyMailReader:
    def __init__(self, conf):
        self.items = []

    def read_mail(self, path):
        content = self.readmail(path)
        soup = BeautifulSoup(content, 'html.parser')
        tables = self.sibling_list(soup, "table")
        #print(soup.prettify())
        #return

        for table in tables:
            self.handle_table(table)

    def readmail(self, path):
        with open(path) as email_file:
            email_message = email.message_from_file(email_file)
        payload=email_message.get_payload()
        encoding=email_message.get_content_charset()
        pbytes = quopri.decodestring(payload)
        final=pbytes.decode(encoding)
        return final

    def get_items(self):
        return self.items

    def paydirt(self, link, msg, desc):
        buffer = ""
        descstr = f"""## CONTEXT from Workflowy mail
* **workflowy link**
  * {link}
"""
        if len(desc):
            descstr = descstr + "* **parent bullets**\n"
            descstr = descstr + "  * " + ("\n  * ".join(desc))
        print(descstr)
        self.items.append(
            MotionTask(name=msg, desc=descstr)
        );

    def handle_table(self, table, parstrs=None):
        if not parstrs:
            parstrs=[]
        trs = self.sibling_list(table, "tr")
        lastmsg=""
        for tr in trs:
            if tr.td and tr.td.has_attr('colspan') and tr.td['colspan'] == "4":
                # 4 colspan == change owner (no action)
                None 
            elif tr.td and tr.td.has_attr('colspan') and tr.td['colspan'] == "3":
                # 3 colspan == contents (possible context or paydirt)
                link = tr.td.a['href']
                span = tr.td.next_sibling.find_all('span')[0]
                msgstr=span.string
                # select if @name matches, and the item is marked green (ie added)
                if (re.search('(\\s|\\b)@'+conf.atname+'(\\b|\\s)', msgstr) and 
                   span.has_attr("style") and
                   re.search('#D5F3E5', span['style'])):
                    self.paydirt(link, msgstr, parstrs)
                lastmsg=msgstr
            elif tr.td and not tr.td.has_attr('colspan'):
                # 0 colspan == new table (descend)
                tds=list(tr.td.next_siblings)
                if tds[2].table:
                    self.handle_table(tds[2].table, parstrs + [lastmsg])
        
    def sibling_list(self, parel, name):
        start = parel.find(name)
        ret = []
        if not start:
            return ret
        ret.append(start)
        ret.extend(start.next_siblings)
        return ret

class WmConf:
    def __init__(self, path):
        with open(path) as jfile:
            conf = json.load(jfile) 
        self.apikey = conf['motion']['apikey']
        self.workspaceId = conf['motion']['workspaceId']
        self.atname = conf['flowymotion']['atname']

conf = WmConf("conf/flowymotion.json");
reader = WorkflowyMailReader(conf)
reader.read_mail("data/workflowy-update2.eml")
writer = MotionTaskWriter(conf, reader.get_items())
writer.write_all()
