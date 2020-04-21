#!groovy
def tryStep(String message, Closure block, Closure tearDown = null) {
    try {
        block();
    }
    catch (Throwable t) {
        slackSend message: "${env.JOB_NAME}: ${message} failure ${env.BUILD_URL}", channel: "#ci-channel-app", color: "danger"
        throw t;
    }
    finally {
        if (tearDown) {
            tearDown();
        }
    }
}

node {
    stage("Checkout") {
        checkout scm
    }

    stage("Test") {
        tryStep "Test", {
            sh "api/deploy/test/test.sh"
        }
    }

    stage("Build dockers") {
        tryStep "build", {
            docker.withRegistry("${DOCKER_REGISTRY_HOST}", "docker_registry_auth") {
                def api = docker.build("datapunt/signals:${env.BUILD_NUMBER}", "api")
                api.push()

                def importer = docker.build("datapunt/signals_importer:${env.BUILD_NUMBER}", "import")
                importer.push()
            }
        }
    }
}

String BRANCH = "${env.BRANCH_NAME}"

if (BRANCH == "master") {
    node {
        stage("Push acceptance image") {
            tryStep "image tagging", {
                docker.withRegistry("${DOCKER_REGISTRY_HOST}", "docker_registry_auth") {
                    def image = docker.image("datapunt/signals:${env.BUILD_NUMBER}")
                    image.pull()
                    image.push("acceptance")
                }
            }
        }
    }

    node {
        stage("Deploy to ACC") {
            tryStep "deployment", {
                build job: "Subtask_Openstack_Playbook",
                parameters: [
                    [$class: "StringParameterValue", name: "INVENTORY", value: "acceptance"],
                    [$class: "StringParameterValue", name: "PLAYBOOK", value: "deploy-signals.yml"],
                ]
            }
        }
    }

    stage("Waiting for approval") {
        slackSend channel: "#ci-channel", color: "warning", message: "Meldingen is waiting for Production Release - please confirm"
        input "Deploy to Production?"
    }

    node {
        stage("Push production image") {
            tryStep "image tagging", {
                docker.withRegistry("${DOCKER_REGISTRY_HOST}", "docker_registry_auth") {
                    def api = docker.image("datapunt/signals:${env.BUILD_NUMBER}")
                    api.pull()
                    api.push("production")
                    api.push("latest")

                    def importer = docker.image("datapunt/signals_importer:${env.BUILD_NUMBER}")
                    importer.pull()
                    importer.push("production")
                    importer.push("latest")
                }
            }
        }
    }

    node {
        stage("Deploy") {
            tryStep "deployment", {
                build job: "Subtask_Openstack_Playbook",
                parameters: [
                        [$class: "StringParameterValue", name: "INVENTORY", value: "production"],
                        [$class: "StringParameterValue", name: "PLAYBOOK", value: "deploy-signals.yml"],
                ]
            }
        }
    }
}
