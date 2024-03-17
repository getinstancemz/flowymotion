# flowymotion

Quick and dirty script to read a Workflowy email (saved as .eml) and to push any new items that mention a specific person (identified in a bullet item by a name with a leading `@` character) to Motion (or Todoist) with some contextual information.

These instructions assume you're using Docker to run this though of course it's not necessary. You can find required packages in `dockerdir/requirements.txt`.

To proceed using Docker, you will need Docker installed and running.

## Download
Grab the environment:

```
git clone git@github.com:getinstancemz/flowymotion.git
cd flowymotion
```

You can work from within the repo directory (`flowymotion`) that this clone will create. If you're using a Docker enviroment as described in this document (ie from `flowymotion/`) then that directory will become available to the container. You should therefore save your Workflowy emails to a subdirectory here so that they can be found by the script.



## Setup
You will need to build the docker image and add some configuration to a file at `conf/flowymotion.json`

### Configuration
You need an API key and a workspace id. You can generate an API key in the [Motion API settings](https://app.usemotion.com/web/settings/api) section. If you do not already have a workspace id, Flowymotion provides a quick tool to list the available workspaces in your account -- see below for that

Copy across the sample configuration file.

```
cp conf/flowymotion.json.sample conf/flowymotion.json
```

Edit the new file -- add your API key to the correct field. If you do not yet have a workspace id, leave the dummy in place for now.

Change the `atname` field to the `@name` you wish the script to search for in Workflow reports in order to generate Motion tasks (do not add `@` in the configuration file -- the script adds that when searching).

### Build the docker image

You will only need to do this once (at least until you clear Docker images).

```
./dockerdir/dbuild
```

This will create a Python image and install requirements for the script. Once this is done you will be able to run the python executable with `./bin/drun`.

### Get a Workspace ID
If you haven't yet got one of these then the system is half-configured. You can already run the script to get a list of available workspaces if you have added your API key.

The script is named `flowymotion`. Here's how to run it with Docker to get a list of workspaces.

```
./bin/drun flowymotion -w
```

Pick a workspace -- by default there will only be one. Copy the id and paste it in to your configuration file, replacing the dummy value. Flowymotion should be fully functional now.

## Running flowymotion
First save your email file somewhere -- if you're running with Docker then this should probably be in a directory under the cloned `flowymotion` directory, since this is mounted. This README assumes you're running from this directory. I will use the `samples/` directory which comes with the repo.

To process an email and push any found tasks to Motion, run with the `-e <path-to-email>` flag -- like this:

```
./bin/drun flowymotion -e samples/workflowy-update1.eml
```

If you want to just check the email parser, then you can run with the dry run flag `-d`


```
./bin/drun flowymotion -d -e samples/workflowy-update1.eml
```

This will read the email and compile the tasks but won't write them to Motion.

**New** If you'd rather use Todoist, you can now do that too -- make sure your api key is added to the configuration file (see the sample) and run with the `-t` flag.

### Getting help.
Run with the `-h` flag:

```
$ ./bin/drun flowymotion -h
usage: flowymotion [-h] [-e  EML] [-d] [-t] [-w]

A bridge that reads a Workflowy update .eml file and adds a Motion task for new lines matching a @name

optional arguments:
  -h, --help          show this help message and exit
  -e  EML, --eml EML  File of type .eml
  -d                  dry run
  -t                  run in todoist mode
  -w, --workspaces    list workspaces
```


