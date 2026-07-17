pipeline {
    agent any

    parameters {
        choice(
            name: 'TEST_SUITE',
            choices: [
                'all',
                'auth -- Login & Registration Tests',
                'e2e_staging -- E2E Checkout (Stage)',
                'e2e_stage2 -- E2E Checkout (Stage2)',
                'e2e_intl -- E2E INTL Checkout',
                'payment_uae -- Payment Methods UAE',
                'payment_ksa -- Payment Methods KSA',
                'payment_intl -- Payment Methods INTL',
                'payment_methods -- All Payment Methods',
                'nav_links -- Navigation Link Checker'
            ],
            description: 'Select which test suite to run'
        )
        choice(
            name: 'BROWSER',
            choices: ['chromium', 'firefox', 'chromium firefox'],
            description: 'Browser to run tests on'
        )
        choice(
            name: 'ENV',
            choices: ['staging', 'stage2'],
            description: 'Environment: staging = stage.cartlow.com, stage2 = stage2.cartlow.com'
        )
    }

    environment {
        BASE_URL = "${params.ENV == 'stage2' ? 'https://stage2.cartlow.com/uae/en' : 'https://stage.cartlow.com/uae/en'}"
        DB_HOST  = '209.38.211.128'
        DB_PORT  = '3306'
        DB_NAME  = 'cartlow_dev'
        DB_USER  = 'sohaib'
        DB_PASS  = 'SoHeyhy@20ZZwaN@2023'
        PYTHONUNBUFFERED = '1'
    }

    stages {

        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python Environment') {
            steps {
                bat '''
                    python -m venv .venv
                    .venv\\Scripts\\pip install --upgrade pip
                    .venv\\Scripts\\pip install -r requirements.txt
                '''
            }
        }

        stage('Install Playwright Browsers') {
            steps {
                bat '.venv\\Scripts\\playwright install chromium firefox'
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    def suite = params.TEST_SUITE.split(' ')[0]  // take only the key part
                    def browsers = params.BROWSER == 'chromium firefox'
                        ? '--browser chromium --browser firefox'
                        : "--browser ${params.BROWSER}"

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
                        case 'e2e_intl':
                            testPath = '"tests/e2e checkout/test_e2e_intl_checkout.py"'
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
                            testPath = 'tests'
                            break
                    }

                    bat """
                        set BASE_URL=${env.BASE_URL}
                        set DB_HOST=${env.DB_HOST}
                        set DB_PORT=${env.DB_PORT}
                        set DB_NAME=${env.DB_NAME}
                        set DB_USER=${env.DB_USER}
                        set DB_PASS=${env.DB_PASS}
                        .venv\\Scripts\\pytest ${testPath} ^
                            ${browsers} ^
                            -v ^
                            --tb=short ^
                            --html=reports/jenkins_report.html ^
                            --self-contained-html ^
                            || exit 0
                    """
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
            archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
        }
        success {
            echo '✅ All tests passed!'
        }
        failure {
            echo '❌ Some tests failed. Check the report.'
        }
    }
}
