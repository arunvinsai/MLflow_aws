import subprocess
import boto3
import mlflow.sagemaker as mfs
import json
import os
from utils.common import read_config


class sagemaker_integration:
    def __init__(self, config=None):
        self.config = read_config(config)

    def upload(self, path_to_artifact=None):
        try:
            
            output = subprocess.run(["aws", "s3", "sync", "{}".format(path_to_artifact),
                                     "s3://{}".format(self.config['aws_s3_bucket_config']['s3_bucket_name']), "--no-verify-ssl"],
                                    stdout=subprocess.PIPE,
                                    encoding='utf-8')
            
            return f"Done Uploading : {output.stdout}"

        except Exception as e:
            return f"Error Occurred While Uploading : {e.__str__()}"

    def deploy_model_aws_sagemaker(self):
        try:
            model_uri = "s3://{}/{}/{}/artifacts/{}/".format(self.config['aws_s3_bucket_config']['s3_bucket_name'],
                                                             self.config['aws_endpoint_config']['experiment_id'],
                                                             self.config['aws_endpoint_config']['run_id'],
                                                             self.config['aws_endpoint_config']['model_name'])
            mfs.deploy(app_name=self.config['aws_sagemaker_config']['app_name'],
                       model_uri=model_uri,
                       execution_role_arn=self.config['sagemaker_role_name']['execution_role_arn'],
                       region_name=self.config['aws_access_config']['region'],
                       image_url=self.config['aws_ecr_config']['image_ecr_url'],
                       mode=mfs.DEPLOYMENT_MODE_CREATE)
            return "Deployment Successfully"
        except Exception as e:
            return f"Error Occurred while Deploying : {e.__str__()} "

    def query(self, input_json):
        try:
            client = boto3.session.Session().client("sagemaker-runtime", self.config['aws_access_config']['region'])
            response = client.invoke_endpoint(
                EndpointName=self.config['aws_sagemaker_config']['app_name'],
                Body=input_json,
                ContentType='application/json; format=pandas-split')
            return json.loads(response['Body'].read().decode("ascii"))
        except Exception as e:
            return f"Error Occurred While Prediction : {e.__str__()}"

    def switching_models(self):
        try:
            new_model_uri = "s3://{}/{}/{}/artifacts/{}/".format(self.config['aws_s3_bucket_config']['s3_bucket_name'],
                                                                 self.config['aws_endpoint_config']['experiment_id'],
                                                                 self.config['aws_endpoint_config']['run_id'],
                                                                 self.config['aws_endpoint_config']['model_name'])

            mfs.deploy(app_name=self.config['aws_sagemaker_config']['app_name'], model_uri=new_model_uri,
                       execution_role_arn=self.config['aws_sagemaker_config']['execution_role_arn'],
                       region_name=self.config['aws_access_config']['region'],
                       image_url=self.config['aws_ecr_config']['image_ecr_url'],
                       mode=mfs.DEPLOYMENT_MODE_REPLACE)

            return f"Model Successfully switched "

        except Exception as e:
            return f"Error While Changing Model : {e.__str__()}"

    def remove_deployed_model(self):
        try:
            mfs.delete(app_name=self.config['aws_sagemaker_config']['app_name'],
                       region_name=self.config['aws_access_config']['region'])
            return f"Endpoint Successfully Deleted : {self.config['aws_sagemaker_config']['app_name']}"
        except Exception as e:
            return f"Error While Deleting EndPoint : {e.__str__()}"