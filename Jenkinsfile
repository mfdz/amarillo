pipeline {
    agent { label 'builtin' }
    environment {
        GITEA_CREDS = credentials('AMARILLO-JENKINS-GITEA-USER')
        TWINE_REPO_URL = "https://git.gerhardt.io/api/packages/amarillo/pypi"
        PLUGINS_REPO_URL = "git.gerhardt.io/api/packages/amarillo/pypi/simple"
        DOCKER_REGISTRY = 'git.gerhardt.io'
        DERIVED_DOCKERFILE = 'standard.Dockerfile'
        OWNER = 'amarillo'
        BASE_IMAGE_NAME = 'amarillo-base'
        IMAGE_NAME = 'amarillo'
        AMARILLO_DISTRIBUTION = '0.3'
        TAG = "${AMARILLO_DISTRIBUTION}.${BUILD_NUMBER}${env.BRANCH_NAME == 'main' ? '' : '-' + env.BRANCH_NAME}"
        DEPLOY_WEBHOOK_URL = "http://amarillo.mfdz.de:8888/${env.BRANCH_NAME}" 
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
        stage('Build base docker image') {
            when {
                isDeployBranch()
            }
            steps {
                echo 'Building image'
                script {
                    docker.build("${OWNER}/${BASE_IMAGE_NAME}:${TAG}")
                }
            }
        }
        stage('Push base image to container registry') {
            when {
                isDeployBranch()
            }
            steps {
                echo 'Pushing image to registry'
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'AMARILLO-JENKINS-GITEA-USER'){
                        def image = docker.image("${OWNER}/${BASE_IMAGE_NAME}:${TAG}")
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }
        stage('Build derived docker image') {
            when {
                isDeployBranch()
            }
            steps {
                echo 'Building image'
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'AMARILLO-JENKINS-GITEA-USER'){
                        docker.build("${OWNER}/${IMAGE_NAME}:${TAG}",
                        //--no-cache to make sure plugins are updated
                        "-f ${DERIVED_DOCKERFILE} --no-cache --build-arg='PACKAGE_REGISTRY_URL=${PLUGINS_REPO_URL}' --build-arg='DOCKER_REGISTRY=${DOCKER_REGISTRY}' --secret id=AMARILLO_REGISTRY_CREDENTIALS,env=GITEA_CREDS .")
                    }

                }
            }
        }
        stage('Push derived image to container registry') {
            when {
                isDeployBranch()
            }
            steps {
                echo 'Pushing image to registry'
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'AMARILLO-JENKINS-GITEA-USER'){
                        def image = docker.image("${OWNER}/${IMAGE_NAME}:${TAG}")
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }
        stage('Notify CD script') {
            when {
                isDeployBranch()
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

def isDeployBranch() {
    return anyOf { branch 'main'; branch 'dev'; branch 'mitanand' }
}
