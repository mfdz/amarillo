pipeline {
    agent any
    environment {
        GITEA_CREDS = credentials('AMARILLO-JENKINS-GITEA-USER')
        PYPI_CREDS = credentials('AMARILLO-JENKINS-PYPI-USER')
        TWINE_REPO_URL = "https://git.gerhardt.io/api/packages/amarillo/pypi"
        PLUGINS_REPO_URL = "git.gerhardt.io/api/packages/amarillo/pypi/simple"
        DOCKER_REGISTRY_URL = 'https://git.gerhardt.io'
        OWNER = 'amarillo'
        IMAGE_NAME = 'amarillo'
        AMARILLO_DISTRIBUTION = '0.1'
        TAG = "${AMARILLO_DISTRIBUTION}.${BUILD_NUMBER}"
        PLUGINS = 'amarillo-metrics amarillo-enhancer amarillo-grfs-export'
        DEPLOY_WEBHOOK_URL = 'http://amarillo.mfdz.de:8888/mitanand'
        DEPLOY_SECRET = credentials('AMARILLO-JENKINS-DEPLOY-SECRET')
    }
    stages {
        stage('Create virtual environment') {
            steps {
                echo 'Creating virtual environment'
                sh '''python3 -m venv .venv
                . .venv/bin/activate'''
                
            }
        }
        stage('Installing requirements') {
            steps {
                echo 'Installing packages'
                sh 'python3 -m pip install -r requirements.txt'
                sh 'python3 -m pip install --upgrade build'
                sh 'python3 -m pip install --upgrade twine'
            }
        }
        stage('Build package') {
            steps {
                echo 'Building package'
                sh 'python3 -m build'
            }
        }
        stage('Publish package to GI') {
            steps {
                sh 'python3 -m twine upload --skip-existing --verbose --repository-url $TWINE_REPO_URL --username $GITEA_CREDS_USR --password $GITEA_CREDS_PSW ./dist/*'              
            }
        }
        stage('Publish package to PyPI') {
            when {
                branch 'release'
            }
            steps {
                sh 'python3 -m twine upload --verbose --username $PYPI_CREDS_USR --password $PYPI_CREDS_PSW ./dist/*'              
            }
        }
        stage('Build Mitanand docker image') {
            when {
                branch 'mitanand'
            }
            steps {
                echo 'Building image'
                script {
                    docker.build("${OWNER}/${IMAGE_NAME}:${TAG}",
                    //--no-cache to make sure plugins are updated
                     "--no-cache --build-arg='PACKAGE_REGISTRY_URL=${PLUGINS_REPO_URL}' --build-arg='PLUGINS=${PLUGINS}' --secret id=AMARILLO_REGISTRY_CREDENTIALS,env=GITEA_CREDS .")
                }
            }
        }
        stage('Push image to container registry') {
            when {
                branch 'mitanand'
            }
            steps {
                echo 'Pushing image to registry'
                script {
                    docker.withRegistry(DOCKER_REGISTRY_URL, 'AMARILLO-JENKINS-GITEA-USER'){
                        def image = docker.image("${OWNER}/${IMAGE_NAME}:${TAG}")
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }
        stage('Notify CD script') {
            when {
                branch 'mitanand'
            }
            steps {
                echo 'Triggering deploy webhook'
                script {
                    def response = httpRequest contentType: 'APPLICATION_JSON',
                        httpMode: 'POST', requestBody: '{}', authentication: 'AMARILLO-JENKINS-DEPLOY-SECRET',
                        url: "${DEPLOY_WEBHOOK_URL}"
                }
            }
        }
    }
}
