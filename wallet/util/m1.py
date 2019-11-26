from flask import current_app
from requests import post


def request_m1finance():
    query = '''
        mutation ($username: String!, $password: String!) {
          authenticate(input: {username: $username, password: $password}) {
            viewer {
              accounts {
                edges {
                  node {
                    name
                    rootPortfolioSlice {
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
          }
        }
    '''
    variables = {
        'username': current_app.config['M1_USERNAME'],
        'password': current_app.config['M1_PASSWORD'],
    }
    json = post('https://lens.m1finance.com/graphql', json={'query': query, 'variables': variables}).json()
    return {edge['node']['name']: edge['node']['rootPortfolioSlice']['performance']
            for edge in json['data']['authenticate']['viewer']['accounts']['edges']}
