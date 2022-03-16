# Specifies base image and tag
# FROM us-docker.pkg.dev/vertex-ai/training/xgboost-cpu.1-1:latest
FROM python:3.7
WORKDIR /root

# Installs additional packages
RUN pip install gcsfs numpy pandas scikit-learn dask distributed xgboost --upgrade

# Copies the trainer code to the docker image.
COPY ./train_xgb.py /root/train_xgb.py

# Sets up the entry point to invoke the trainer.
ENTRYPOINT ["python3", "train_xgb.py"]
