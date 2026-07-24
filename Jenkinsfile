pipeline {
    agent any

    triggers {
        githubPush()
    }

    parameters {
        choice(
            name: 'TEST_SUITE',
            choices: [
                'all',
                'auth -- Login & Registration Tests',
                'e2e_staging -- E2E Checkout (Stage)',
                'e2e_stage2 -- E2E Checkout (Stage2)',
                'payment_methods -- All Payment Methods',
                'payment_uae -- Payment Methods UAE',
                'payment_ksa -- Payment Methods KSA',
                'payment_intl -- Payment Methods INTL',
                'nav_links -- Navigation Link Checker'
            ],
            description: 'Select which test suite to run'
        )
        choice(
            name: 'BROWSER',
            choices: ['chromium', 'firefox', 'chromium firefox'],
            description: 'Browser to use'
        )
        choice(
            name: 'ENV',
            choices: ['staging', 'stage2'],
            description: 'staging = stage.cartlow.com | stage2 = stage2.cartlow.com'
        )
        booleanParam(
            name: 'USE_DOCKER',
            defaultValue: false,
            description: 'Run tests inside Docker container'
        )
    }

    environment {
        BASE_URL         = "${params.ENV == 'stage2' ? 'https://stage2.cartlow.com/uae/en' : 'https://stage.cartlow.com/uae/en'}"
        DB_HOST          = '209.38.211.128'
        DB_PORT          = '3306'
        DB_NAME          = 'cartlow_dev'
        DB_USER          = 'sohaib'
        DB_PASS          = 'SoHeyhy@20ZZwaN@2023'
        PYTHONUNBUFFERED = '1'
        IMAGE_NAME       = 'cartlow-playwright'
    }

    stages {

        stage('Checkout Code') {
            steps {
                checkout scm
                echo "Branch: ${env.GIT_BRANCH} | Commit: ${env.GIT_COMMIT}"
            }
        }

        stage('Build Docker Image') {
            when {
                expression { return params.USE_DOCKER }
            }
            steps {
                bat "docker build -t ${env.IMAGE_NAME} ."
            }
        }

        stage('Setup Python') {
            when {
                expression { return !params.USE_DOCKER }
            }
            steps {
                bat '''
                    python -m venv .venv
                    .venv\\Scripts\\pip install --upgrade pip
                    .venv\\Scripts\\pip install -r requirements.txt
                    .venv\\Scripts\\playwright install chromium firefox
                '''
            }
        }

        stage('Run Tests') {
            steps {
                catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE') {
                    script {
                        def suite    = params.TEST_SUITE ? params.TEST_SUITE.split(' ')[0] : 'all'
                        def browsers = params.BROWSER == 'chromium firefox'
                            ? '--browser chromium --browser firefox'
                            : "--browser ${params.BROWSER ?: 'chromium'}"

                        def testPath = ''
                        switch(suite) {
                            case 'auth':
                                testPath = '"tests/auth module testing/test_login.py" "tests/auth module testing/test_registration_positive.py"'
                                break
                            case 'e2e_staging':
                                testPath = '"tests/e2e checkout/test_all_channels_e2e.py"'
                                break
                            case 'e2e_stage2':
                                testPath = '"tests/e2e checkout/test_all_channels_e2e_stage2.py"'
                                break
                            case 'payment_uae':
                                testPath = '"tests/test payment method/test_payment_method_uae.py"'
                                break
                            case 'payment_ksa':
                                testPath = '"tests/test payment method/test_payment_method_ksa.py"'
                                break
                            case 'payment_intl':
                                testPath = '"tests/test payment method/test_payment_method_intl.py"'
                                break
                            case 'payment_methods':
                                testPath = '"tests/test payment method"'
                                break
                            case 'nav_links':
                                testPath = '"tests/auth module testing/test_nav_links.py"'
                                break
                            case 'all':
                            default:
                                testPath = '"tests/auth module testing/test_login.py" "tests/auth module testing/test_registration_positive.py" "tests/e2e checkout/test_all_channels_e2e.py" "tests/test payment method"'
                                break
                        }

                        if (params.USE_DOCKER) {
                            bat """
                                docker run --rm ^
                                    -e BASE_URL=${env.BASE_URL} ^
                                    -e DB_HOST=${env.DB_HOST} ^
                                    -e DB_PORT=${env.DB_PORT} ^
                                    -e DB_NAME=${env.DB_NAME} ^
                                    -e DB_USER=${env.DB_USER} ^
                                    -e DB_PASS=${env.DB_PASS} ^
                                    -v "%cd%\\reports:/app/reports" ^
                                    ${env.IMAGE_NAME} ^
                                    python -m pytest ${testPath} ${browsers} ^
                                        -v --tb=short ^
                                        --html=reports/jenkins_report.html ^
                                        --self-contained-html ^
                                        --junit-xml=reports/results.xml
                            """
                        } else {
                            bat """
                                set BASE_URL=${env.BASE_URL}
                                set DB_HOST=${env.DB_HOST}
                                set DB_PORT=${env.DB_PORT}
                                set DB_NAME=${env.DB_NAME}
                                set DB_USER=${env.DB_USER}
                                set DB_PASS=${env.DB_PASS}
                                .venv\\Scripts\\pytest ${testPath} ${browsers} ^
                                    -v --tb=short ^
                                    --html=reports/jenkins_report.html ^
                                    --self-contained-html ^
                                    --junit-xml=reports/results.xml
                            """
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            publishHTML(target: [
                allowMissing: true,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports',
                reportFiles: 'jenkins_report.html',
                reportName: 'Playwright Test Report'
            ])
            junit allowEmptyResults: true, testResults: 'reports/results.xml'
            archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
            echo "Build #${env.BUILD_NUMBER} | ${currentBuild.currentResult} | Report: ${env.BUILD_URL}Playwright_20Test_20Report"
        }
        success  { echo '✅ All tests PASSED!' }
        unstable { echo '⚠️  Some tests FAILED — check report.' }
        failure  { echo '❌ Pipeline FAILED — check console.' }
    }
}
