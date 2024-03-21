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
        if not self.conf.motion_configured():
            print("Can't check Motion for workspaces -- not configured\n")
            return
        response = requests.get("https://api.usemotion.com/v1/workspaces",
            headers={'X-API-Key': self.conf.motionkey})
        json_response = response.json()
        response.raise_for_status()
        for space in json_response['workspaces']:
            print(f"* {space['id']} {space['name']}")

class TodoistTaskWriter:
    def __init__(self, conf, tasks):
        self.conf = conf 
        self.tasks = tasks
    def write_all(self):
        print("\nADDING TASKS - Todoist\n")
        if not self.conf.todoist_configured():
            print("Can't write to Todoist -- not configured\n")
            return
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
        print("\nADDING TASKS -- Motion\n")
        if not self.conf.motion_configured() or not self.conf.motiondefault:
            print("Can't write to Motion -- not configured\n")
            return
        for task in self.motiontasks:
            self.write_task(task)

    def write_task(self, task):
        payload = {
            "workspaceId": self.conf.motiondefault,
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
                'X-API-Key': self.conf.motionkey,
                'Content-Type': 'application/json'
            })
        response_json = response.json()
        response.raise_for_status()
        print(f"* added: {response_json['id']} / {response_json['name']}")

class Reader:
    def match_atname(self, atname, teststr):
        atnames=atname.split(",")
        for atname in atnames:
            if re.search(r'(^|\s|\b)@' + atname + r'(\b|\s|$)', teststr, re.I):
                return True
        return False

class TextReader(Reader):
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
            end=idx+3
            start = 0 if start < 0 else start
            end = len(lines) if end > len(lines)-1 else end
            #if re.search('(^|\\s|\\b)@'+self.conf.atname+'(\\b|\\s|$)', line, re.I):
            if self.match_atname(self.conf.atname, line):
                #print(f"{start}:{idx}:{end}")
                self.paydirt(line, lines[start:end])
            idx=idx+1
        #print(self.items)

    def paydirt(self, msg, desc):
        buffer = ""
        descstr = f"""## CONTEXT from Text File
"""
        if len(desc):
            descstr = descstr + "* **extract**\n"
            descstr = descstr + "> " + ("\n> ".join(desc))
        msg = re.sub(r'^\s*\*\s+', '', msg)
        task = MotionTask(name=msg, desc=descstr)
        print("name: "+msg)
        print("deadline: " + task.deadline+"\n")
        print("desc:\n" + descstr+"\n")
        self.items.append(task);

    def get_items(self):
        return self.items

class WorkflowyMailReader(Reader):
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
                #if (re.search('(^|\\s|\\b)@'+self.conf.atname+'(\\b|\\s|$)', msgstr, re.I) and 
                if (self.match_atname(self.conf.atname, msgstr) and 
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
    def __init__(self, path, handle=None):
        with open(path) as jfile:
            conf = json.load(jfile) 
        if  not handle:
            self.atname = conf['flowymotion']['atname']
        else:
            self.atname = handle

        self.motionkey = None
        self.motiondefault = None
        if 'motion' in conf.keys():
            self.motionkey = conf['motion']['apikey']
            self.motiondefault = conf['motion']['workspaceId']

        self.todoistkey = None
        self.todoistdefalut = None
        if 'todoist' in conf.keys():
            self.todoistkey = conf['todoist']['apikey']
            self.todoistdefault = conf['todoist']['default-project']

    def motion_configured(self):
        if self.motionkey:
            return True
        return False

    def todoist_configured(self):
        if self.todoistkey:
            return True
        return False

