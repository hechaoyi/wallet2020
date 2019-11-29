from flask import current_app
from requests import post

URL = 'https://lens.m1finance.com/graphql'


def get_accounts():
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
    json = post(URL, json={'query': query, 'variables': variables}).json()
    return {edge['node']['name']: edge['node']['rootPortfolioSlice']['performance']
            for edge in json['data']['authenticate']['viewer']['accounts']['edges']}


def screen_securities(min_cap=None, min_pe=None, max_pe=None):
    def screen(after):
        query = '''
            query ($after: String, $minCap: Float, $minPE: Float, $maxPE: Float) {
              viewer {
                screenSecurities(
                  filterTypes: EQUITY,
                  limit: [{type: MARKET_CAP, min: $minCap}, {type: PE_RATIO, min: $minPE, max: $maxPE}],
                  sort: {type: MARKET_CAP, direction: DESC},
                  after: $after, first: 100
                ) {
                  pageInfo {
                    hasNextPage
                    endCursor
                  }
                  edges {
                    node {
                      symbol
                    }
                  }
                }
              }
            }
        '''
        variables = {'after': after, 'minCap': min_cap, 'minPE': min_pe, 'maxPE': max_pe}
        json = post(URL, json={'query': query, 'variables': variables}).json()
        page = json['data']['viewer']['screenSecurities']['pageInfo']
        return ([n['node']['symbol'].replace('.', '-')
                 for n in json['data']['viewer']['screenSecurities']['edges']],
                page['endCursor'] if page['hasNextPage'] else None)

    min_cap = min_cap * 1000000000 if min_cap else None
    symbols, cursor = screen(None)
    while cursor and len(symbols) < 400:
        s, cursor = screen(cursor)
        symbols += s
    return symbols


def screen_funds(*category, min_cap=1, max_exp=1):
    query = '''
        query ($category: [String!], $minCap: Float, $maxExp: Float) {
          viewer {
            screenFunds(
              filterCategory: $category,
              limit: [{type: FUND_TOTAL_ASSETS, min: $minCap}, {type: FUND_NET_EXPENSE_RATIO, max: $maxExp}],
              sort: {type: FUND_TOTAL_ASSETS, direction: DESC},
              first: 100
            ) {
              edges {
                node {
                  symbol
                }
              }
            }
          }
        }
    '''
    min_cap = min_cap * 1000000000 if min_cap else None
    variables = {'category': category, 'minCap': min_cap, 'maxExp': max_exp}
    json = post(URL, json={'query': query, 'variables': variables}).json()
    return [n['node']['symbol'].replace('.', '-')
            for n in json['data']['viewer']['screenFunds']['edges']]
