pipeline {
    agent { label 'builtin' }
    environment {
        GITEA_CREDS = credentials('AMARILLO-JENKINS-GITEA-USER')
        PYPI_CREDS = credentials('AMARILLO-JENKINS-PYPI-USER')
        TWINE_REPO_URL = "https://git.gerhardt.io/api/packages/amarillo/pypi"
        PLUGINS_REPO_URL = "https://git.gerhardt.io/api/packages/amarillo/pypi/simple"
        PYPI_REPO_URL = "https://pypi.org/simple"
        DOCKER_REGISTRY = 'git.gerhardt.io'
        DERIVED_DOCKERFILE = 'standard.Dockerfile'
        MITANAND_DOCKERFILE = 'mitanand.Dockerfile'
        OWNER = 'amarillo'
        BASE_IMAGE_NAME = 'amarillo-base'
        IMAGE_NAME = 'amarillo'
        MITANAND_IMAGE_NAME = 'amarillo-mitanand'
        AMARILLO_DISTRIBUTION = '2.0.0'
        TAG = "${AMARILLO_DISTRIBUTION}${env.BRANCH_NAME == 'main' ? '' : '-' + env.BRANCH_NAME}-${BUILD_NUMBER}"
        DEPLOY_WEBHOOK_URL = "http://amarillo.mfdz.de:8888/dev"
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
                branch 'main'
            }
            steps {
                sh 'python3 -m twine upload --verbose --username $PYPI_CREDS_USR --password $PYPI_CREDS_PSW ./dist/*'              
            }
        }
        stage('Build base docker image') {
            steps {
                echo 'Building image'
                script {
                    docker.build("${OWNER}/${BASE_IMAGE_NAME}:${TAG}")
                }
            }
        }
        stage('Push base image to container registry') {
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
            steps {
                echo 'Building image'
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'AMARILLO-JENKINS-GITEA-USER'){
                        docker.build("${OWNER}/${IMAGE_NAME}:${TAG}",
                        //--no-cache to make sure plugins are updated
                        "-f ${DERIVED_DOCKERFILE} --no-cache --build-arg='PACKAGE_REGISTRY_URL=${env.BRANCH_NAME == 'main' ? env.PYPI_REPO_URL : env.PLUGINS_REPO_URL}' --build-arg='DOCKER_REGISTRY=${DOCKER_REGISTRY}' --secret id=AMARILLO_REGISTRY_CREDENTIALS,env=GITEA_CREDS .")
                    }

                }
            }
        }
        stage('Push derived image to container registry') {
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

        stage('Build mitanand docker image') {
            steps {
                echo 'Building image'
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'AMARILLO-JENKINS-GITEA-USER'){
                        docker.build("${OWNER}/${MITANAND_IMAGE_NAME}:${TAG}",
                        //--no-cache to make sure plugins are updated
                        "-f ${MITANAND_DOCKERFILE} --no-cache --build-arg='PACKAGE_REGISTRY_URL=${env.BRANCH_NAME == 'main' ? env.PYPI_REPO_URL : env.PLUGINS_REPO_URL}' --build-arg='DOCKER_REGISTRY=${DOCKER_REGISTRY}' --secret id=AMARILLO_REGISTRY_CREDENTIALS,env=GITEA_CREDS .")
                    }

                }
            }
        }
        stage('Push mitanand image to container registry') {
            steps {
                echo 'Pushing image to registry'
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'AMARILLO-JENKINS-GITEA-USER'){
                        def image = docker.image("${OWNER}/${MITANAND_IMAGE_NAME}:${TAG}")
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }
        // stage('Notify CD script') {
        //     when {
        //         not {
        //             branch 'main'
        //         }
        //     }
        //     steps {
        //         echo 'Triggering deploy webhook'
        //         script {
        //             def response = httpRequest contentType: 'APPLICATION_JSON',
        //                 httpMode: 'POST', requestBody: '{}', authentication: 'AMARILLO-JENKINS-DEPLOY-SECRET',
        //                 url: "${DEPLOY_WEBHOOK_URL}"
        //         }
        //     }
        // }
    }
}