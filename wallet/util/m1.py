from flask import current_app
from requests import post


def request_m1finance():
    query = '''
        mutation ($username: String!, $password: String!, $account: ID!) {
          authenticate(input: {username: $username, password: $password}) {
            viewer {
              anyNode(id: $account) {
                ... on RootPortfolioSlice {
                  performance(period: ONE_DAY) {
                    startValue {
                      date
                      value
                    }
                    endValue {
                      date
                      value
                    }
                    moneyWeightedRateOfReturn
                    totalGain
                    capitalGain
                    earnedDividends
                    netCashFlow
                  }
                }
              }
            }
          }
        }
    '''
    variables = {
        'username': current_app.config['M1_USERNAME'],
        'password': current_app.config['M1_PASSWORD'],
        'account': current_app.config['M1_ACCOUNT']
    }
    json = post('https://lens.m1finance.com/graphql', json={'query': query, 'variables': variables}).json()
    return json['data']['authenticate']['viewer']['anyNode']['performance']
