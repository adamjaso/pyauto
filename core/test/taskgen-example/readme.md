# Using Taskgen

## Generate raw tasks

```
python -m pyauto.core.taskgen tasks.yml values.yml
```

## Generate usable config

```
python -m pyauto.core.template -f tasks.yml values.yml -i config.j2 -o result.yml
```

## Run config

### View all steps in deploy_all task

```
python -m pyauto.core.deploy -c result.yml -i deploy_all
```

### Run all steps in deploy_all task

```
python -m pyauto.core.deploy -c result.yml deploy_all
```
