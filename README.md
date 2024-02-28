# flowymotion

Quick and dirty script to read a Workflowy email (saved as .eml) and to push any new items to Motion with some contextual information.

These instructions assume you're using Docker to run this. You will need Docker installed and running.

## Quick start.

Add configuration. You need an apikey and a workspace id. (See below on getting those).

```
cp conf/flowymotion.ini.sample conf/flowymotion.ini
```

Edit the new file.

Set up the Docker image

```
./dockerdir/dbuild
```

And you're set. You can run the script (this will change soon) -- like this:

```
./bin/drun flowymotion.py
```


