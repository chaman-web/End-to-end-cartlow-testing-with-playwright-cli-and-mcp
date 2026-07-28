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
                'intl_regression -- INTL Full Regression',
                'intl_homepage -- INTL Homepage',
                'intl_search -- INTL Search',
                'intl_pdp -- INTL PDP',
                'intl_gift_card -- INTL Gift Card PDP',
                'intl_cart -- INTL Cart',
                'intl_checkout -- INTL Checkout',
                'intl_shipping -- INTL Shipping Fee',
                'intl_payment -- INTL Payment Flow',
                'intl_journey -- INTL Full Journey (E2E)',
                'auth -- Login & Registration',
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
            choices: ['staging', 'stage2', 'production'],
            description: 'staging = stage.cartlow.com | stage2 = stage2.cartlow.com | production = cartlow.com'
        )
        string(
            name: 'WORKERS',
            defaultValue: '4',
            description: 'Number of parallel workers (pytest-xdist -n). Set to 1 to disable parallelism.'
        )
        booleanParam(
            name: 'USE_DOCKER',
            defaultValue: false,
            description: 'Run tests inside Docker container'
        )
        booleanParam(
            name: 'HEADED',
            defaultValue: false,
            description: 'Run browser in headed mode (only works outside Docker)'
        )
    }

    environment {
        ENV              = "${params.ENV ?: 'staging'}"
        PYTHONUNBUFFERED = '1'
        IMAGE_NAME       = 'cartlow-playwright'
        // Credentials loaded from Jenkins credential store — never hardcoded
        TEST_EMAIL       = credentials('cartlow-test-email')
        TEST_PASSWORD    = credentials('cartlow-test-password')
    }

    stages {

        stage('Checkout Code') {
            steps {
                checkout scm
                echo "Branch: ${env.GIT_BRANCH} | Commit: ${env.GIT_COMMIT} | ENV: ${env.ENV}"
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
                        def suite   = params.TEST_SUITE ? params.TEST_SUITE.split(' ')[0] : 'all'
                        def workers = params.WORKERS ? params.WORKERS.trim() : '4'
                        def headed  = params.HEADED ? '--headed' : ''

                        def browsers = params.BROWSER == 'chromium firefox'
                            ? '--browser chromium --browser firefox'
                            : "--browser ${params.BROWSER ?: 'chromium'}"

                        // ── Suite → test path mapping ──────────────────────
                        def testPath = ''
                        switch(suite) {
                            // INTL Regression
                            case 'intl_regression':
                                testPath = '"tests/intl regression"'
                                break
                            case 'intl_homepage':
                                testPath = '"tests/intl regression/test_intl_homepage.py"'
                                break
                            case 'intl_search':
                                testPath = '"tests/intl regression/test_intl_search.py"'
                                break
                            case 'intl_pdp':
                                testPath = '"tests/intl regression/test_intl_pdp.py"'
                                break
                            case 'intl_gift_card':
                                testPath = '"tests/intl regression/test_intl_gift_card_pdp.py"'
                                break
                            case 'intl_cart':
                                testPath = '"tests/intl regression/test_intl_cart.py"'
                                break
                            case 'intl_checkout':
                                testPath = '"tests/intl regression/test_intl_checkout_page.py"'
                                break
                            case 'intl_shipping':
                                testPath = '"tests/intl regression/test_intl_shipping_fee.py"'
                                break
                            case 'intl_payment':
                                testPath = '"tests/intl regression/test_intl_payment_flow.py"'
                                break
                            case 'intl_journey':
                                testPath = '"tests/intl regression/test_intl_full_journey.py"'
                                break
                            // Auth
                            case 'auth':
                                testPath = '"tests/auth module testing"'
                                break
                            // E2E
                            case 'e2e_staging':
                                testPath = '"tests/e2e checkout/test_all_channels_e2e.py"'
                                break
                            case 'e2e_stage2':
                                testPath = '"tests/e2e checkout/test_all_channels_e2e_stage2.py"'
                                break
                            // Payment Methods
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
                            // All
                            case 'all':
                            default:
                                testPath = 'tests'
                                break
                        }

                        def parallelFlag = workers == '1' ? '' : "-n ${workers} --dist=loadfile"
                        def commonArgs   = """${testPath} ${browsers} ${headed} ${parallelFlag} -v --tb=short --html=reports/jenkins_report.html --self-contained-html --junit-xml=reports/results.xml"""

                        if (params.USE_DOCKER) {
                            bat """
                                docker run --rm ^
                                    -e ENV=${env.ENV} ^
                                    -e TEST_EMAIL=${env.TEST_EMAIL} ^
                                    -e TEST_PASSWORD=${env.TEST_PASSWORD} ^
                                    -v "%cd%\\reports:/app/reports" ^
                                    ${env.IMAGE_NAME} ^
                                    python -m pytest ${commonArgs}
                            """
                        } else {
                            bat """
                                set ENV=${env.ENV}
                                set TEST_EMAIL=${env.TEST_EMAIL}
                                set TEST_PASSWORD=${env.TEST_PASSWORD}
                                .venv\\Scripts\\pytest ${commonArgs}
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
                allowMissing         : true,
                alwaysLinkToLastBuild: true,
                keepAll              : true,
                reportDir            : 'reports',
                reportFiles          : 'jenkins_report.html',
                reportName           : 'Playwright Test Report'
            ])
            junit allowEmptyResults: true, testResults: 'reports/results.xml'
            archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
            echo "Build #${env.BUILD_NUMBER} | ${currentBuild.currentResult} | Suite: ${params.TEST_SUITE} | ENV: ${env.ENV}"
            echo "Report: ${env.BUILD_URL}Playwright_20Test_20Report"
        }
        success  { echo '✅ All tests PASSED!' }
        unstable { echo '⚠️  Some tests FAILED — check the HTML report.' }
        failure  { echo '❌ Pipeline FAILED — check console output.' }
    }
}
