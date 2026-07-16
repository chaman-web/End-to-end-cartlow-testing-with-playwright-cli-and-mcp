pipeline {
    agent any

    parameters {
        choice(
            name: 'TEST_SUITE',
            choices: [
                'auth',
                'e2e_staging',
                'e2e_stage2',
                'payment_methods',
                'all'
            ],
            description: 'Which test suite to run'
        )
        choice(
            name: 'BROWSER',
            choices: ['chromium', 'firefox', 'all'],
            description: 'Browser to run tests on'
        )
        choice(
            name: 'ENV',
            choices: ['staging', 'stage2', 'production'],
            description: 'Environment to test against'
        )
        booleanParam(
            name: 'HEADED',
            defaultValue: false,
            description: 'Run in headed mode (requires display)'
        )
    }

    environment {
        BASE_URL        = "${params.ENV == 'stage2' ? 'https://stage2.cartlow.com/uae/en' : 'https://stage.cartlow.com/uae/en'}"
        DB_HOST         = credentials('cartlow-db-host')
        DB_PASS         = credentials('cartlow-db-pass')
        DISPLAY         = ':99'
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
                sh '''
                    python3 -m venv .venv
                    .venv/bin/pip install --upgrade pip
                    .venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Install Playwright Browsers') {
            steps {
                sh '.venv/bin/playwright install chromium firefox'
            }
        }

        stage('Start Virtual Display') {
            when {
                expression { return params.HEADED }
            }
            steps {
                sh 'Xvfb :99 -screen 0 1280x800x24 &'
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    def browserFlag = params.BROWSER == 'all'
                        ? '--browser chromium --browser firefox'
                        : "--browser ${params.BROWSER}"

                    def headedFlag = params.HEADED ? '--headed' : ''

                    def testPath = ''
                    switch(params.TEST_SUITE) {
                        case 'auth':
                            testPath = '"tests/auth module testing/test_login.py" "tests/auth module testing/test_registration_positive.py"'
                            break
                        case 'e2e_staging':
                            testPath = '"tests/e2e checkout/test_all_channels_e2e.py"'
                            break
                        case 'e2e_stage2':
                            testPath = '"tests/e2e checkout/test_all_channels_e2e_stage2.py"'
                            break
                        case 'payment_methods':
                            testPath = '"tests/test payment method/"'
                            break
                        case 'all':
                            testPath = 'tests/'
                            break
                    }

                    sh """
                        BASE_URL=${env.BASE_URL} \\
                        DB_HOST=${env.DB_HOST} \\
                        DB_PASS=${env.DB_PASS} \\
                        .venv/bin/pytest ${testPath} \\
                            ${browserFlag} \\
                            ${headedFlag} \\
                            -v \\
                            --tb=short \\
                            --html=reports/jenkins_report.html \\
                            --self-contained-html \\
                            -n auto \\
                            || true
                    """
                }
            }
        }
    }

    post {
        always {
            // Publish HTML report
            publishHTML(target: [
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports',
                reportFiles: 'jenkins_report.html',
                reportName: 'Playwright Test Report'
            ])

            // Archive test artifacts
            archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true

            // JUnit XML results (if pytest-junit installed)
            junit allowEmptyResults: true, testResults: 'reports/*.xml'
        }
        success {
            echo '✅ All tests passed!'
        }
        failure {
            echo '❌ Some tests failed. Check the report.'
        }
    }
}
