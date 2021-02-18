"""
This is an algorithm to implement a simple buy & hold strategy on AlgoDynamix-tracked indices.
To avoid numerous orders, set initial portfolio value to e.g. $100000.
"""
import quantopian.algorithm as algo
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.filters import StaticSids
from quantopian.pipeline.factors import Latest, SimpleMovingAverage
import quantopian.optimize as opt

# my_stocks = symbols(['SIZE','MTUM','VLUE','QUAL','GLD','SPY','QQQ','DIA','TLT','CQQQ','IBB'])
my_stocks = [44543, 44542, 44546, 45104, 26807, 8554, 19920, 2174, 23921, 39035, 22445]


def initialize(context):
    # Define stocks to buy
    context.stocks_to_buy = set([sid(44543), sid(44542), sid(44546), sid(45104), sid(26807), sid(8554), sid(19920), sid(2174), sid(23921), sid(39035), sid(22445)])
    
    # Make pipeline
    algo.attach_pipeline(make_pipeline(), 'pipeline')
    
    # Dictionary of desired stock numbers
    context.stock_numbers = {}
    
    # Record tracking variables at the end of each day.
    algo.schedule_function(
        record_vars,
        algo.date_rules.every_day(),
        algo.time_rules.market_close(),
    )


def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Documentation
    on pipeline can be found here:
    https://www.quantopian.com/help#pipeline-title
    """

    # Custom universe containing only desired assets (stocks with flag data)
    universe = StaticSids(my_stocks)

    pipe = Pipeline(
        columns={
            'close': USEquityPricing.close.latest,
        },
        screen=universe
    )
    return pipe
    
    
def handle_data(context, data):
    """
    Execute orders every minute.
    """
    weight = 1.0/len(my_stocks)
    
    if context.stocks_to_buy:
        context.output = algo.pipeline_output('pipeline')
        for asset, row in context.output.iterrows():
            if asset not in context.stock_numbers:
                context.stock_numbers[asset] = int(context.portfolio.starting_cash * weight / row.close)
    
    for asset, shares in context.stock_numbers.items():
        if asset in context.stocks_to_buy:
            if not get_open_orders(asset):
                order_target(asset, shares)
            if context.portfolio.positions[asset].amount == shares:
                context.stocks_to_buy.remove(asset)
        
        
def record_vars(context, data):
    """
    Record positions in portfolio.
    """
    print(context.stocks_to_buy)
    for asset, position in context.portfolio.positions.items():
        log.info(str(asset) + ": " + str(position.amount * position.last_sale_price))