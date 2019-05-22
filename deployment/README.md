# Django app setup on AWS

## Introduction

The deployment is using elastic beanstalk on AWS to setup and manage the resources (postgres database, ec2 instances,...). Using the AWS CLI and the elastic beanstalk CLI, the entire setup can be configured.

## Installation requirements

To perform these actions, the [AWS CLI](https://aws.amazon.com/cli/) and [eb CLI](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3.html) are required. Furthermore, make sure to have the AWS authentification and profiles defined for DEV and/or PRD environment.

The elastic beanstalk cli initialization is done using  `eb init`, from which custom adaptations were added (inside the `.ebextensions` and `.elasticbeanstalk` folders). When you want to start using elastic beanstalk for the vespawatch, you have to link the initialization with vespawatch application. Execute the command `eb init` in the same folder as the `.ebextensions`, choose `eu-west-1 : EU (Ireland)` and select the vespawatch application when prompted. Say No to using AWS Code Commit.

The tutorial underneath starts from these existing components to create a new environment and provide new deployments.

## Deployment required files

To provide the deployment to AWS using  elastic beanstalk, the following elements are required. First of all, the elastic beanstalk configurations:

- `.elasticbeanstalk`, created by the `eb init` command  containing general config
- `.ebextensions`, containing the django specific elements and steps during deployment (location of the settings file, database migration steps,...

Next, some policies required to setup the application:
- `ec2-trust-policy.json`: assume role of the instance profile, so policies can be linked to ec2 instances.
- `s3-policy.json`: policy to access the vespawatch bucket, which is linked to the ec2 instances running the application
- `ec2-describetags.json`: Required to extract the identifiers of the running instances and get the first in row to run cron jobs (and not on all instances)
- `cloudwatch-write-logs.json`: policy to write custom logs to cloudwatch
- `s3-tags.json`: tags to indicate the bucket with, required for the admin and cost calculation

## Setup

In general, to create a new environment (dev/prd), following steps are required just a **single time**:

1. Create *key-pair* combination for the EC2 instances
2. Create a *S3 bucket* to store the media files (uploaded photos)
3. Create a custom *instance profile* (role) to attach to the EC2 instances, providing eb policies and S3 bucket access
4. Create the *elastic beanstalk environment*  containing the ec2 instances, database,...

Next, new deployments can be done whenever required using the deployment command:

```
# deploy
eb deploy vespawatch-xxx --message  "informative message..."
```
### Key-pair combination

It is straightforward to create a new key-pair combination using the AWS Console > EC2 > Key Pairs > `Create Key Pair`.
For development, the key-pair combination is called `LW-INBO-VESPAWATCH`, which can be used as name both in DEV and PRD. For UAT it is called `LW-INBO-VESPAWATCH-UAT`.

Do not forget to put the key-pair combination in the team-folder location.

### S3 Bucket creation

To store the media files (i.e. uploaded images), we use a S3 Bucket. To create the S3 Bucket and add the appropriate tags to it:

```
aws s3api create-bucket --bucket lw-vespawatch-prd --region eu-west-1 --create-bucket-configuration LocationConstraint=eu-west-1 --acl private
aws s3api put-bucket-tagging --bucket lw-vespawatch-prd --tagging file://s3-tags.json
```
For more info, see https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings

Django uses the S3 as a backend using the `django-storages` package, see https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings

Furthermore, to make sure photos in the page fragments can be stored with their filename (no temporary granted query string) in the database (for other images this is not an issue), access to the images is granted from the domain using a `GetObject` S3 bucket policy. For example, the prd-environment:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AddPerm",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::lw-vespawatch-uat/*",
            "Condition": {
                "StringLike": {
                    "aws:Referer": "https://vespawatch.be/*"
                }
            }
        }
    ]
}
```
For uat the `Referer` becomes "https://uat.vespawatch.be/*".

### Prepare the ec2 instance profile (role) to access the S3 bucket and manage eb admin

Without providing a `instance-role`, the default is used. However, as we have multiple eb running at inbo, the default instance role (what the EC2 machine is allowed to do) would get mixed permissions attached to it. Hence, we define a custom Instance role and attach the S3 permissions to it:

* create the instance profile for vespawatch
* create a custom role with the S3 access to vespawatch permission
* add the policies from `aws-elasticbeanstalk-ec2-role` (default for EC2s in eb) to the custom role
* attach custom role to the instance profile

```
# create the custom instance profile
aws iam create-instance-profile --instance-profile-name aws-elasticbeanstalk-ec2-role-vespawatch

# create a custom vespawatch aws-elasticbeanstalk-ec2-role
aws iam create-role --role-name aws-elasticbeanstalk-ec2-role-vespawatch --assume-role-policy-document file://ec2-trust-policy.json --description 'vespawatch application role'

# add the S3 access rule
aws iam put-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-name lw-vespawatch-s3 --policy-document file://s3-policy.json
# add the ec2 instance tag query option
aws iam put-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-name lw-vespawatch-ec2tags --policy-document file://deployment/ec2-describetags.json
# add the custom logs to cloudwatch permission
aws iam put-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-name lw-vespawatch-write-cloudwatch --policy-document file://deployment/cloudwatch-write-logs.json

# add the required elasticbeanstalk policies (taken from aws-elasticbeanstalk-ec2-role)
aws iam attach-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-arn arn:aws:iam::aws:policy/AWSElasticBeanstalkWebTier
aws iam attach-role-policy --role-name aws-elasticbeanstalk-ec2-role-vespawatch --policy-arn arn:aws:iam::226308051916:policy/AWS-Beanstalk-Volumes

# attach the custom vespawatch aws-elasticbeanstalk-ec2-role
aws iam add-role-to-instance-profile --instance-profile-name aws-elasticbeanstalk-ec2-role-vespawatch --role-name aws-elasticbeanstalk-ec2-role-vespawatch
```

To get an overview of the instance profiles, check `aws iam list-instance-profiles`

More info on the instance profile creation is provided here:
* https://docs.aws.amazon.com/cli/latest/reference/iam/create-instance-profile.html
* https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/iam-instanceprofile.html
* https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2_instance-profiles.html

**Notice**: As an instance profile can only be linked to a single role, we create a new role with the permissions of the elastic beanstalk default `aws-elasticbeanstalk-ec2-role` role and our own custom policy to access the S3 Bucket.

### create environment

The setup is different in development versus production, as the subnets, security groups and key-pair combination are different. Also on the django side, some configuration settings (settings are contained inside `djangoproject/djangoproject/settings` folder) are different. This `settings.py` file is referenced inside the `.ebextensions` folder settings to retrieve the settings.

The `settings.py file` configurations that are environment specific are adjusted using the environmental variable `ENVIRONMENT` (with one of the values`dev`, `uat` or `prd`).

For *development*, the environment creation is done with the following command:
```
eb create
--cname vespawatch-dev
--database --database.username $DB_USER --database.password $DB_PWD
--elb-type classic
--envvars SECRET_KEY=$DJANGO_SECRET_KEY,VESPA_SU_NAME=$VESPA_SU_NAME,VESPA_SU_PWD=$VESPA_SU_PWD,DB_USER=$DB_USER,DB_PWD=$DB_PWD,ENVIRONMENT=dev
--region eu-west-1
--vpc
--vpc.dbsubnets subnet-2b338273,subnet-2ce39448,subnet-d0c6a5a6
--vpc.ec2subnets subnet-8c4dfcd4,subnet-fef98e9a,subnet-c8fc9fbe
--vpc.elbsubnets subnet-8c4dfcd4,subnet-fef98e9a,subnet-c8fc9fbe
--vpc.id vpc-cc8610a8
--vpc.securitygroups sg-ca7ae0b2,sg-4b8f442d
--tags APPLICATION=VESPAWATCH,ENVIRONMENT=DEV,OWNER=LIFEWATCH-VESPAWATCH,BUSINESS_UNIT=LIFEWATCH,COST_CENTER=EVINBO,RUNDECK=TRUE
--instance_profile aws-elasticbeanstalk-ec2-role-vespawatch
```
For *uat*, the environment creation is done with the following command:
```
eb create
--cname vespawatch-uat
--database --database.username $DB_USER --database.password $DB_PWD
--database.size 5
--database.engine postgres
--elb-type classic
--envvars SECRET_KEY=$DJANGO_SECRET_KEY,VESPA_SU_NAME=$VESPA_SU_NAME,VESPA_SU_PWD=$VESPA_SU_PWD,DB_USER=$DB_USER,DB_PWD=$DB_PWD,ENVIRONMENT=uat
--region eu-west-1
--vpc
--vpc.dbsubnets subnet-f54dfcad,subnet-14f98e70,subnet-e7fc9f91
--vpc.ec2subnets subnet-994afbc1,subnet-5cf98e38,subnet-2efc9f58
--vpc.elbsubnets subnet-994afbc1,subnet-5cf98e38,subnet-2efc9f58
--vpc.id vpc-a58610c1
--vpc.securitygroups sg-cf47ddb7,sg-8a9346ec
--instance_profile aws-elasticbeanstalk-ec2-role-vespawatch
--keyname LW-INBO-VESPAWATCH-UAT
--tags APPLICATION=VESPAWATCH,ENVIRONMENT=UAT,OWNER=LIFEWATCH-VESPAWATCH,BUSINESS_UNIT=LIFEWATCH,COST_CENTER=EVINBO,RUNDECK=TRUE
```

For *production*, the environment creation is done with the following command:
```
eb create
--cname vespawatch-prd
--database --database.username $DB_USER --database.password $DB_PWD
--elb-type classic
--envvars SECRET_KEY=$DJANGO_SECRET_KEY,VESPA_SU_NAME=$VESPA_SU_NAME,VESPA_SU_PWD=$VESPA_SU_PWD,DB_USER=$DB_USER,DB_PWD=$DB_PWD,ENVIRONMENT=$ENVIRONMENT,INAT_APP_SECRET=$INAT_APP_SECRET
--region eu-west-1
--vpc
--vpc.dbsubnets subnet-7a763f23,subnet-c4f6ffa1,subnet-9a0a3bed
--vpc.ec2subnets subnet-78763f21,subnet-c5f6ffa0,subnet-9c0a3beb
--vpc.elbsubnets subnet-78763f21,subnet-c5f6ffa0,subnet-9c0a3beb
--vpc.id vpc-79d0f71c
--vpc.securitygroups sg-ce6ff5b6,sg-35d5ed51
--tags APPLICATION=VESPAWATCH,ENVIRONMENT=PRD,OWNER=LIFEWATCH-VESPAWATCH,BUSINESS_UNIT=LIFEWATCH,COST_CENTER=EVINBO,RUNDECK=TRUE
--instance_profile aws-elasticbeanstalk-ec2-role-vespawatch
```

Note the additional environmental variable `INAT_APP_SECRET` for production to enable push access to the Inaturalist app, which is only used in production.


Prompt will provide some additional questions:

```
Enter Environment Name
(default is vespawatch-dev):
```
just accept the default here by enter.

Next:
```
Do you want to associate a public IP address? (Y/n): n
Do you want the load balancer to be public? (Select no for internal) (Y/n): n
```
As these will be handled by the reverse proxy of INBO, this is handles by operations (Bert) and we do not use public ip addresses.

**Notice**: Information on the subnets, vpc and security groups are provided within the console or in the config files of https://github.com/inbo/cloudformation-templates/tree/master/config/vpc

More information on the `eb-create` command, see https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb3-create.html.

## Deploy the django app

When the environment works, the deployment of the application is done by:

```
# redeploy
eb deploy vespawatch-xxx --message "your informatice message"
```

`vespawatch-xxx` is the environment you want to deploy to.

## Bash script for deployment

A small deployment bash script has been prepared to execute the steps above. To execute the setup, make sure your aws profile is set correctly (dev or prd) and execute the script (adapt the capital arguments with more useful names and store these securely):

```
./deployment/setup.sh dev DB_USERNAME DB_PASSWORD KEEPTHISDJANGOKEYSECRET APP_SU_USERNAME APP_SU_PASSWORD DUMMY
```

or

```
./deployment/setup.sh prd DB_USERNAME DB_PASSWORD KEEPTHISDJANGOKEYSECRET APP_SU_USERNAME APP_SU_PASSWORD INAT_API_SECRET
```


Variables:
* `$ENVIRONMENT` e.g. 'dev' (or 'uat', 'prd')
* `$DB_USER` RDS database user
* `$DB_PWD`   RDS database pwd
* `$DJANGO_SECRET_KEY`   django app secret key
* `$VESPA_SU_NAME`  user name vespawatch applicatie superuser
* `$VESPA_SU_PWD` password vespawatch applicatie superuser
* `$INAT_APP_SECRET` (only relevant for production) password

Possible improvement: https://medium.com/@nqbao/how-to-use-aws-ssm-parameter-store-easily-in-python-94fda04fea84

Some more steps are required when doing the setup, see next sections.

## Post first-deployment steps

These steps need to be done just a single time after the initial deployment.

### Setup the firefighters polygons and accounts

With the proper authentification rights enabled, we can appply some additional steps during the first requirement. These commands are not included as container commands, as they only need to be configured during the first deployment, whereas the steps in the `01_python_config` file will run each new deployment

```
eb ssh --command "source /opt/python/run/venv/bin/activate  python manage.py import_firefighters_zones data/Brandweerzones_2019.geojson"
eb ssh --command "source /opt/python/run/venv/bin/activate && python manage.py create_firefighters_accounts"
```

If those commands would not work as such, they can be executed from any instance as well after ssh to the instance. In order to run the django manage commands, the proper environment and sudo rights should be provided:

```
sudo su
source /opt/python/run/venv/bin/activate
source /opt/python/current/env
cd /opt/python/current/app
python manage.py import_firefighters_zones data/Brandweerzones_2019.geojson
python manage.py create_firefighters_accounts
```

Optional (when encountering thumbnail errors), use the `python manage.py generateimages` command as well.

### Adapt the security group excluding inbound rule

Check the group-id of the security group, e.g. `g-0ed982b15ae8893ef` and revoke the ssh inbound rule on this security group:

```
aws ec2 revoke-security-group-ingress --group-id sg-0ed982b15ae8893ef --protocol tcp --port 22 --cidr 0.0.0.0/0
```

### Extend the database backup period

So, if the identifier of the created database is `aa6isov6zpwhro`, the extension to 7 days is achieved by:

```
modify-db-instance --db-instance-identifier aa6isov6zpwhro --backup-retention-period 7
```

## Alarm setup vespawatch module

To inform the django developers about errors on the application side, setting up an SNS topic to subscribe and the cloudwatch alerts is explained in this section.

### Setup an SNS topic so maintainers can subscribe

Call the topic `lw-vespawatch-alerts`

```
aws sns create-topic --name lw-vespawatch-alerts
```

Using the received arn, subscribe with the chosen maintainer mailing addresses:

```
aws sns subscribe --topic-arn arn:aws:sns:eu-west-1:xxxxxxxx --protocol email --notification-endpoint stijn.vanhoey@inbo.be
```

See also: https://docs.aws.amazon.com/cli/latest/userguide/cli-services-sns.html

### Setup alarms and publish them to the SNS

This requires the extraction of information from the logs using a specific filter and the publishing of alarms. Multiple metrics can be relevant or setup in time. The django logging settings provide django logs using the following format: `{levelname} {asctime} {module} {process:d} {thread:d} {message}` with the `{levelname}` either `WARNING`, `ERROR` or `CRITICAL` (at least on UAT/PRD, see [documentation](https://docs.djangoproject.com/en/2.1/topics/logging/) for other options on dev-level).

For example, the warning that no favicon is found is resulting in the following message: `WARNING 2019-03-15 11:57:32,277 log 21720 140268024583936 Not Found: /favicon.ico`

To setup (mail) alerts when `ERROR` or `CRITICAL` messages are reported, we can setup an approproate filter and create an alarm when any of these occur:

#### Create metric filter(s)

We create two filters, one for counting the number of occurrences of `CRITICAL` and one for `ERROR` on the UAT log group (!adapt for PRD!):

```
aws logs put-metric-filter --log-group-name /aws/elasticbeanstalk/vespawatch-uat/opt/python/log/django.log --filter-name  vespawatch_critical --filter-pattern "CRITICAL" --metric-transformations metricName=vespawatch_critical_count,metricNamespace=vespawatch_logs,metricValue=1,defaultValue=0

aws logs put-metric-filter --log-group-name /aws/elasticbeanstalk/vespawatch-uat/opt/python/log/django.log --filter-name  vespawatch_error --filter-pattern "ERROR" --metric-transformations metricName=vespawatch_error_count,metricNamespace=vespawatch_logs,metricValue=1,defaultValue=0
```

For production, adjust the `log-group-name` to the vespawatch environment name.

Note: `metricValue=1` is the count increase when an occurrence is detected

#### Adjust retention time of the logs

By default, logs are stored forever. This is not required as 3 months of logs will suffice to check the behaviour. Adjusting the log retention time for the django group. For example for the uat `django.log` log group in UAT (!adapt for PRD!):

```
aws logs put-retention-policy --log-group-name /aws/elasticbeanstalk/vespawatch-uat/opt/python/log/django.log --retention-in-days 90
```

#### Create alarm on filter and publish to SNS

To create the alarm, link it to the defined metric and namespace and provide the SNS topic as `alarm-action`:

```
aws cloudwatch put-metric-alarm --alarm-name vespawatch_critical --alarm-description "Alarm on CRITICAL messages from vespawatch website"  --metric-name vespawatch_critical_count  --namespace vespawatch_logs  --statistic Sum  --period 300  --threshold 0 --comparison-operator GreaterThanThreshold --evaluation-periods 1 --alarm-actions arn:aws:sns:eu-west-1:226308051916:lw-vespawatch-alerts --treat-missing-data notBreaching

aws cloudwatch put-metric-alarm --alarm-name vespawatch_error --alarm-description "Alarm on ERROR messages from vespawatch website"  --metric-name vespawatch_error_count  --namespace vespawatch_logs  --statistic Sum  --period 300  --threshold 0 --comparison-operator GreaterThanThreshold --evaluation-periods 1 --alarm-actions arn:aws:sns:eu-west-1:226308051916:lw-vespawatch-alerts --treat-missing-data notBreaching
```

See also: https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/put-metric-alarm.html and https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html do not use the `--unit Count` option with this kind of setup (although it seems logical), as this will not result in proper switch to ALARM.


## Backups

- All **code** is under version control and each deployment is stored in a S3 bucket managed by elastic beanstalk
- Backups of the **RDS** are managed on organisation level of INBO.
- Backups of the **media files** in the S3 bucket is not considered.

## Troubleshooting

### Logs

Different logs are sent to AWS cloudwatch and an email-alert is provided when django logs contain ERROR or CRITICAL. Further troubleshooting will sometimes be required. To login to a current running instance, you can use the `eb ssh` (with the environemnt specified) command, assuming your `.pem`-file is properly stored. For example, to login to UAT:

```
eb ssh vespawatch-uat
```

When troubleshooting on the server itself, there are a few directories you should be aware of:

* `/opt/python`: Root of where you application will end up.
* `/opt/python/current/app`: The current application that is hosted in the environment.
* `/opt/python/on-deck/app`: The app is initially put in on-deck and then, after all the deployment is complete, it will be moved to current. If you are getting failures in your container_commands, check out out the on-deck folder and not the current folder.
* `/opt/python/current/env`: All the env variables that eb will set up for you. If you are trying to reproduce an error, you may first need to source `/opt/python/current/env` to get things set up as they would be when eb deploy is running.
* `opt/python/run/venv`: The virtual env used by your application; you will also need to run source `/opt/python/run/venv/bin/activate` if you are trying to reproduce an error.

Hence, the log files to screen:
* The `/opt/python/log/django.log` file contains the django warning and error information and will be your first entry point for app related information
* `var/log` contains the general logging files, e.g. the access and erro logs in the `httpd` folder.

Notice that the logs (also `django.log`) are accessible using the AWS eb console as well by requesting the logs (all or last 100 lines).

### Database

The backup setup of the RDS is creates automated backups of last 7 days. However, in case of management on the environment, when testing queries,... on the prd-database or just to import the prd-dbase for local development, make an additional dump. To do so, make a connection to the database first, which can be done by using port-forwarding the dbase instance to you localhost

```
ssh YOUR_ACCOUNT@BASTION_IP -2 -4 -i YOUR_ACCOUNT.pem -N -L 127.0.1:54321:DBASE_ENDPOINT:5432
```

with:
- `YOUR_ACCOUNT` the AWS account user name
- `BASTION_IP` the ip address from the bastion server
- `YOUR_ACCOUNT.pem` the path of your locally stored (read-only) pem file
- `DBASE_ENDPOINT` the endpoint of the database

Note, the `127.0.1:54321` is just chosen. When portforwarding is active, the `pg_xxx` commands can be used on the remote database.

```
pg_dump --format=c -n public --verbose --host=127.0.0.1 --port=54321 --username=USERNAME DB_NAME > dump-vespawatch.backup
```

with:
- `USERNAME` the database superuser username
- `DB_NAME` the database name (probably `vespawatch`)

which stored the database in to the file `dump-vespawatch.backup`. To setup a new local database using the dump:

```
createdb DB_NAME
pg_restore -v -d DB_NAME dump-vespawatch.backup
```

with:
- `DB_NAME` the database name (probably `vespawatch` or alike).

### Recreate the environment

A regular redeployment (provide correct `settings.py` file and run `eb deploy ENV-NAME`) does only redeploy the code to the instances and does not affect the RDS. In the (rare) occurrence of a complete failure of the environment, the rebuilding or entire resetup of the application could be required.

__IMPORTANT:__ Rebuilding an elastic beanstalk environment with an Amazon RDS database instance creates a new database with the same configuration, but __does not apply a snapshot__ to the new database!

In order to rebuild an environment from scratch, the procedure above remains largely the same (assuming the S3 buckets and policies - not part of the eb environment - will still exists) except of the __database__, which need to be created from an AWS snapshot and/or manual export (see previous section).

Make sure to create a snapshot before deleting any environment. The snapshot can be used as such in the new environment. The main difference is the additional step of providing the database in between the environment creation (`eb create`) and the effective deployment (`eb deploy`) instead of creating a new database on the environment creation.

1. Create a new environment without database, this means use the `eb create` command but without `--database --database.username $DB_USER --database.password $DB_PWD` line, for example:

```
eb create
--cname vespawatch-prd
--elb-type classic
--envvars SECRET_KEY=$DJANGO_SECRET_KEY,VESPA_SU_NAME=$VESPA_SU_NAME,VESPA_SU_PWD=$VESPA_SU_PWD,DB_USER=$DB_USER,DB_PWD=$DB_PWD,ENVIRONMENT=$ENVIRONMENT,INAT_APP_SECRET=$INAT_APP_SECRET
--region eu-west-1
--vpc
--vpc.dbsubnets subnet-7a763f23,subnet-c4f6ffa1,subnet-9a0a3bed
--vpc.ec2subnets subnet-78763f21,subnet-c5f6ffa0,subnet-9c0a3beb
--vpc.elbsubnets subnet-78763f21,subnet-c5f6ffa0,subnet-9c0a3beb
--vpc.id vpc-79d0f71c
--vpc.securitygroups sg-ce6ff5b6,sg-35d5ed51
--tags APPLICATION=VESPAWATCH,ENVIRONMENT=PRD,OWNER=LIFEWATCH-VESPAWATCH,BUSINESS_UNIT=LIFEWATCH,COST_CENTER=EVINBO,RUNDECK=TRUE
--instance_profile aws-elasticbeanstalk-ec2-role-vespawatch
```
As the creation will also call the config with the migration of the database (which is not existing), the environment will initiate errors. Ignore these for now.

2.  Using the AWS Console, attach the database snapshot to the environment, as described in the [AWS docs](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/using-features.managing.db.html)
3. Once database is restored (this takes a while), redeploy the application with `eb deploy`.


## Setup and configuration info

### Geo-django

The usage of [geo-django](https://docs.djangoproject.com/en/2.1/ref/contrib/gis/) supporting geographic functionalities requires additional dependencies. On the database side, this requires the Postgis extension to Postgres, which is by default available when using the AWS postgres RDS.

On the application side, the EC2 servers need to have the `gdal/geos/proj` suite available. Installing `gdal` and `proj` using `yum` is only possible when activating the `epel`  repository. As such, these are included as the first container command in the `01_python.config` file instead of the general list of yum packages in the `02_packages.config`.

## Further info and useful links

* https://realpython.com/deploying-a-django-app-and-postgresql-to-aws-elastic-beanstalk/
* https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-container.html
