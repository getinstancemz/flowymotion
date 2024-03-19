import requests
import email
import json 
import quopri
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
#from dateutil.parser import parse
import re

class MotionTask:
    def __init__(self, name, desc):
        now = datetime.now()
        expire = now + timedelta(days=7)
        self.name=name
        self.desc=desc
        self.startday=now.strftime("%Y-%m-%d")
        self.startdate=now.strftime("%Y-%m-%dT%H:%M:%S")
        self.deadline=expire.strftime("%Y-%m-%dT%H:%M:%S")

    def __repr__(self):
        return f"name: {self.name} / desc: {self.desc}"

    def __str__(self):
        return f"name: {self.name} / desc: {self.desc}"

class MotionWorkspaceReader:
    def __init__(self, conf):
        self.conf = conf 

    def readWorkspaces(self):
        print("\nREADING MOTION WORKSPACES\n")
        response = requests.get("https://api.usemotion.com/v1/workspaces",
            headers={'X-API-Key': self.conf.apikey})
        json_response = response.json()
        response.raise_for_status()
        for space in json_response['workspaces']:
            print(f"* {space['id']} {space['name']}")

class TodoistTaskWriter:
    def __init__(self, conf, tasks):
        self.conf = conf 
        self.tasks = tasks
    def write_all(self):
        print("\nADDING TASKS\n")
        for task in self.tasks:
            self.write_task(task)

    def write_task(self, task):
        payload = {
            "content": task.name,
            "description": task.desc,
            "due_date": task.startday,
            "duration": 60,
            "duration_unit": "minute",
        }
        response = requests.post("https://api.todoist.com/rest/v2/tasks",
            json=payload,
            headers={
                'Authorization': 'Bearer '+self.conf.todoistkey,
                'Content-Type': 'application/json'
            })
        response_json = response.json()
        response.raise_for_status()
        print(f"* added: {response_json['id']} / {response_json['content']}")


class MotionTaskWriter:
    def __init__(self, conf, motiontasks):
        self.conf = conf 
        self.motiontasks = motiontasks
    def write_all(self):
        print("\nADDING TASKS\n")
        for task in self.motiontasks:
            self.write_task(task)

    def write_task(self, task):
        payload = {
            "workspaceId": self.conf.workspaceId,
            "name": task.name,
            "description": task.desc,
            "dueDate": task.deadline,
            "autoScheduled": {
                "startDate": task.startdate,
                "deadlineType": "SOFT",
                "schedule": "Work Hours"
            }
        }
        response = requests.post("https://api.usemotion.com/v1/tasks",
            json=payload,
            headers={
                'X-API-Key': self.conf.apikey,
                'Content-Type': 'application/json'
            })
        response_json = response.json()
        response.raise_for_status()
        print(f"* added: {response_json['id']} / {response_json['name']}")

class TextReader:
    def __init__(self, conf):
        self.items = []
        self.conf = conf

    def process(self, path):
        print("\nPROCESSING Text FILE\n")
        content = self.readfile(path)

    def readfile(self, path):
            
        with open(path) as text_file:
            lines = text_file.read().splitlines()
        idx=0
        for line in lines:
            start=idx-2
            end=idx+2
            start = 0 if start < 0 else start
            end = len(lines)-1 if end >= len(lines)-1 else end
            if re.search('(^|\\s|\\b)@'+self.conf.atname+'(\\b|\\s|$)', line):
                self.paydirt(line, lines[start:end])
            idx=idx+1
        #print(self.items)

    def paydirt(self, msg, desc):
        buffer = ""
        descstr = f"""## CONTEXT from Text File
"""
        if len(desc):
            descstr = descstr + "* **extract**\n"
            descstr = descstr + "  * " + ("\n  * ".join(desc))
        task = MotionTask(name=msg, desc=descstr)
        print("name: "+msg)
        print("deadline: " + task.deadline+"\n")
        print("desc:\n" + descstr+"\n")
        self.items.append(task);

    def get_items(self):
        return self.items



class WorkflowyMailReader:
    def __init__(self, conf):
        self.items = []
        self.conf = conf

    def process(self, path):
        print("\nPROCESSING MAIL FILE\n")
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
        task = MotionTask(name=msg, desc=descstr)
        print("name: "+msg)
        print("deadline: " + task.deadline+"\n")
        print("desc:\n" + descstr+"\n")
        self.items.append(task);

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
                # TODO - maybe descend and test all sub spans.
                # for now we only work with the top span
                msgstr=span.get_text()
                # select if @name matches, and the item is marked green (ie added)
                #print(msgstr)
                if (re.search('(^|\\s|\\b)@'+self.conf.atname+'(\\b|\\s|$)', msgstr) and 
                   span.has_attr("style") and
                   re.search('#D5F3E5', span['style'])
                   ):
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
        self.todoistkey = conf['todoist']['apikey']
        self.todoistdefault = conf['todoist']['default-project']


