# deployment_tasks.py

# this needs to be imported so that the config class will be registered
import deployment_config


def deploy_app(config, app_name):
    # implement deployment here
    print('deploying {0}...'.format(app_name))
    app = config.apps.get_tag(app_name)
    print(app)

