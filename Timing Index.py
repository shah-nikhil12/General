import quantopian.algorithm as algo
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.data.user_5f1c029707e06c0012eb30db import algo_data_full, flag_counts, up_ratios_2
from quantopian.pipeline.filters import StaticAssets, StaticSids
import quantopian.optimize as opt
from datetime import datetime
import math

# Large cap growth JKE
# Large cap value JKF
# Mid cap growth JKH
# Mid cap value JKI
# Small cap growth JKK
# Small cap value JKL

#my_stocks = symbols(['SPY', 'QQQ', 'JKE', 'JKF', 'JKH', 'JKI', 'JKK', 'JKL'])
my_stocks = [8554, 19920, 26444, 26445, 26447, 26448, 26454, 26451]

def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    # Create our dynamic stock selector.
    algo.attach_pipeline(make_pipeline(), 'pipeline')
    
    # Dictionary of max weights for each asset.
    # Weight by mean annual return % of flags.
    context.max_weights = {
        sid(8554): 0.15, # SPY
        sid(19920): 0.20, # QQQ
        sid(26444): 0.17, # JKE
        sid(26445): 0.13, # JKF
        sid(26447): 0.12, # JKH
        sid(26448): 0.13, # JKI
        sid(26454): 0.10, # JKK
        sid(26451): 0.0 # JKL
    }
    
    # Dictionary of target weights for each asset.
    context.target_weights = {}
    
    # Dictionary of target number of shares for each asset.
    context.target_shares = {}
    
    # Dictionary of flags for each month for each asset.
    # Each entry for each asset is {'UP': x, 'DOWN': y}
    context.flags = {}
    
    # Dictionary of latest prices for each asset.
    context.price = {}
    
    # Dictionary of latest UP ratios for each asset.
    context.up_ratios = {}
    
    # Set of assets that have recevied first multiple down flag sequence.
    context.first_down_sequence = set()
    
    # First iteration: initialize weightings etc.
    context.first_iteration = True
    
    # Overweighting: True in 2020
    context.overweighting = False

    # Record tracking variables at the end of each day.
    algo.schedule_function(
        record_vars,
        algo.date_rules.every_day(),
        algo.time_rules.market_close(),
    )
    
    # Place orders at the end of each month.
    algo.schedule_function(
        place_orders,
        algo.date_rules.month_end()
    )
    


def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline).
    """

    # Custom universe containing only desired assets (stocks with flag data)
    universe = StaticSids(my_stocks)

    return Pipeline(
        columns={
            #'flag_type': algo_data_full.flag_type.latest,
            #'flag_price': algo_data_full.flag_price.latest,
            #'end_flag_date': algo_data_full.end_flag_date.latest,
            #'end_flag_price': algo_data_full.end_flag_price.latest,
            'up_flags': flag_counts.up.latest,
            'down_flags': flag_counts.down.latest,
            'up_ratio': up_ratios_2.up_ratio.latest,
            'close': USEquityPricing.close.latest,
        },
        screen=universe
    )


def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = algo.pipeline_output('pipeline')

    # These are the securities that we are interested in trading each day.
    context.security_list = context.output.index
    
    # Loop through all assets in pipeline.
    for asset, row in context.output.iterrows():
        context.price[asset] = row.close
        """
        # Skip entries with no flags.
        if row.flag_type != 'UP' and row.flag_type != 'DOWN':
            continue
        
        log.info('%s flag for %s. Price level = %f' % (row.flag_type, asset, context.price[asset]))
        
        # Count flags for asset in context.flags
        if asset in context.flags:
            context.flags[asset][row.flag_type] += 1
        else:
            if row.flag_type == 'UP':
                context.flags[asset] = {'UP': 1, 'DOWN': 0}
            
            elif row.flag_type == 'DOWN':
                context.flags[asset] = {'UP': 0, 'DOWN': 1}
        """ 
            
        context.up_ratios[asset] = row.up_ratio
            
        if math.isnan(row.up_flags):
            continue
        
        context.flags[asset] = {'UP': row.up_flags, 'DOWN': row.down_flags}
        
        # In 2020, activate overweighting
        if not context.overweighting:
            today = get_datetime('US/Eastern')
            if today.year == 2020:
                context.overweighting = True

        
def rebalance_weightings(context):
    """
    Calculate max weightings for each asset using UP ratios.
    """
    total_ratio = 0
    log.info("*******Rebalancing weightings********")
    print(context.up_ratios)
    
    for asset, ratio in context.up_ratios.items():
        total_ratio += ratio
        
    for asset, ratio in context.up_ratios.items():
        context.max_weights[asset] = ratio/total_ratio
    
    log.info(context.max_weights)

        
def place_orders(context, data):
    """
    Place orders at the end of every month.
    """
    log.info("*********Monthly flags: %s" % context.flags)
    
    context.sell = []
    context.buy = []
   
    # Go through flags to determine buy/sell signals
    for asset, flags in context.flags.items():
        # If up > down and multiple blue flags, add to buy
        if flags['UP'] > flags['DOWN'] and flags['UP'] > 1:
            context.buy.append(asset)
            
        # If down > up and multiple down flags, add to sell
        elif flags['DOWN'] > flags['UP'] and flags['DOWN'] > 1:
            context.sell.append(asset)
            
    # If both SPY and QQQ are buys, rebalance weightings and check components
    if sid(8554) in context.buy and sid(19920) in context.buy:
        rebalance_weightings(context)
        
        # Reset down sequence
        context.first_down_sequence = set()
        
        # Reset SPY and QQQ to max weightings
        context.target_weights[sid(8554)] = context.max_weights[sid(8554)]
        context.target_weights[sid(19920)] = context.max_weights[sid(19920)]
        
        # Convert weights to number of shares   
        context.target_shares[sid(8554)] = round(context.target_weights[sid(8554)] * context.portfolio.portfolio_value / context.price[sid(8554)])
        context.target_shares[sid(19920)] = round(context.target_weights[sid(19920)] * context.portfolio.portfolio_value / context.price[sid(19920)])
        
        # If not overweighting:
        if not context.overweighting:
            context.buy.remove(sid(8554))
            context.buy.remove(sid(19920))
        
        # Check components
        for asset, ratio in context.up_ratios.items():
            # If UP ratio > 1, add to buy
            if asset != sid(8554) and asset != sid(19920) and ratio > 1:
                context.buy.append(asset)
    
    # If SPY is a sell, check UP ratios for components
    if sid(8554) in context.sell:
        for asset, ratio in context.up_ratios.items():
            # If UP ratio < 1, add to sell
            if asset != sid(8554) and asset != sid(19920) and ratio < 1:
                context.sell.append(asset)
    
    
    
    # First month at end August 2017: set all other assets to max weighting, except take UP ratio of JKL to be <1 so sell 20% of weighting
    if context.first_iteration:
        log.info('First iteration')
        
        # Initialise weightings
        rebalance_weightings(context)
        context.first_iteration = False
        
        for asset, weight in context.max_weights.items():        
            # JKL
            if asset == sid(26451):
                context.sell.append(asset)

            context.target_weights[asset] = weight
                
            # Convert weights to number of shares   
            context.target_shares[asset] = round(context.target_weights[asset] * context.portfolio.portfolio_value / context.price[asset])
    
    buy_overweight = []
    remaining_cash = context.portfolio.cash
    
    # Buy components first (before considering overweighting QQQ/SPY)
    for asset in sorted(context.buy, reverse=True):
        
        # This is an up sequence so no subsequent down sequence
        if asset in context.first_down_sequence:
            context.first_down_sequence.remove(asset)            
        
        # Buy 50% of weighting
        log.info('UP flags for %s: Buy 50 percent' % asset)
        extra_weight = 0.5 * context.max_weights[asset]
            
        # Do not exceed max shares by weighting, UNLESS taking from cash from components (overweighting)
        if context.target_weights[asset] == context.max_weights[asset] or (context.target_weights[asset] > context.max_weights[asset] and context.overweighting):
            buy_overweight.append(asset)
        
        elif context.target_weights[asset] + extra_weight > context.max_weights[asset]:
            context.target_weights[asset] = context.max_weights[asset]
            
        else:
            context.target_weights[asset] += extra_weight
            
        # Convert weights to number of shares
        old_shares = context.target_shares[asset]
        context.target_shares[asset] = round(context.target_weights[asset] * context.portfolio.portfolio_value / context.price[asset])
        remaining_cash -= (context.target_shares[asset] - old_shares) * context.price[asset]
    
    for asset in buy_overweight:
        if remaining_cash > 0:
            # If first overweight or 2 assets to be overweighted, take 50% of available cash
            if context.target_weights[asset] > context.max_weights[asset] or len(buy_overweight) > 1:
                log.info('Taking half of cash of value: %f' % (remaining_cash * 0.5))
                context.target_weights[asset] += 0.5 * remaining_cash / context.portfolio.portfolio_value
            
            # If second overweight, take all remaining cash
            else:
                log.info('Taking remaining of cash of value: %f' % (remaining_cash))
                context.target_weights[asset] += remaining_cash / context.portfolio.portfolio_value
             
        else:
            # If no cash, ignore
            log.info('UP flags for %s: No change' % asset)
            continue
    
            
    # For assets in sell list
    for asset in context.sell:
        
        # If asset already has 0 holdings, ignore
        if context.target_weights[asset] == 0:
            log.info('DOWN flags for %s: No change' % asset)
            continue
        
        # If first multiple down flags, sell 20% of UP weight
        elif asset not in context.first_down_sequence:
            log.info('First DOWN flags for %s: Sell 20 percent' % asset)
            context.target_weights[asset] -= 0.2 * context.max_weights[asset]
            context.first_down_sequence.add(asset)
                
        # If this is a subsequent down flag sequence, sell 40% of UP weight
        else:
            log.info('DOWN flags for %s: Sell 40 percent' % asset)
            context.target_weights[asset] -= 0.4 * context.max_weights[asset]
            
        # Ensure no short position
        if context.target_weights[asset] < 0:
            context.target_weights[asset] = 0
            
        # Convert weights to number of shares   
        context.target_shares[asset] = round(context.target_weights[asset] * context.portfolio.portfolio_value / context.price[asset])
                
    print(context.target_weights)      
    
        
def handle_data(context, data):
    """
    Called every minute.
    """
    for asset, shares in context.target_shares.items():
        if not get_open_orders(asset):
            order = order_target(asset, shares)
            #if order != None:
                #print("Target shares: %d of %s. Ordering %d shares. Current %d shares." % (shares, asset, get_order(order).amount, context.portfolio.positions[asset].amount))



def record_vars(context, data):
    """
    Record number of positions in portfolio.
    """
    # Get total position values for each asset
    try:
        spy_pos = context.portfolio.positions[sid(8554)]
        spy_value = spy_pos.amount * spy_pos.last_sale_price
    except:
        spy_value = 0
        
    try:
        qqq_pos = context.portfolio.positions[sid(19920)]
        qqq_value = qqq_pos.amount * qqq_pos.last_sale_price
    except:
        qqq_value = 0
    
    record('SPY', spy_value, 'QQQ', qqq_value, 'Cash', context.portfolio.cash, 'Portfolio', context.portfolio.portfolio_value)