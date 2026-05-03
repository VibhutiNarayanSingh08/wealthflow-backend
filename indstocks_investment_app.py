"""
IndStocks Investment Application
A comprehensive investment management system using IndStocks API
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
try:
    import pandas as pd
except ImportError:
    pd = None

class IndStocksInvestment:
    def __init__(self, access_token: str):
        self.base_url = 'https://api.indstocks.com'
        self.headers = {
            'Authorization': access_token,
            'Content-Type': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_user_profile(self) -> Dict:
        """Get user profile and account details"""
        try:
            response = self.session.get(f'{self.base_url}/user/profile')
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching profile: {e}")
            return {}
    
    def get_market_quotes_full(self, scrip_codes: List[str]) -> Dict:
        """Get comprehensive market data including OHLC, volume, etc."""
        try:
            params = {'scrip-codes': ','.join(scrip_codes)}
            response = self.session.get(f'{self.base_url}/market/quotes/full', params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching full quotes: {e}")
            return {}
    
    def get_ltp(self, scrip_codes: List[str]) -> Dict:
        """Get last traded prices"""
        try:
            params = {'scrip-codes': ','.join(scrip_codes)}
            response = self.session.get(f'{self.base_url}/market/quotes/ltp', params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching LTP: {e}")
            return {}
    
    def get_market_depth(self, scrip_codes: List[str]) -> Dict:
        """Get market depth (order book) data"""
        try:
            params = {'scrip-codes': ','.join(scrip_codes)}
            response = self.session.get(f'{self.base_url}/market/quotes/mkt', params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching market depth: {e}")
            return {}
    
    def get_portfolio_holdings(self) -> Dict:
        """Get current portfolio holdings"""
        try:
            response = self.session.get(f'{self.base_url}/portfolio/holdings')
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching holdings: {e}")
            return {}
    
    def get_portfolio_positions(self, segment: str = None, product: str = None) -> Dict:
        """Get current positions with optional filters"""
        try:
            params = {}
            if segment:
                params['segment'] = segment
            if product:
                params['product'] = product
            
            response = self.session.get(f'{self.base_url}/portfolio/positions', params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching positions: {e}")
            return {}
    
    def place_smart_order(self, order_details: Dict) -> Dict:
        """Place advanced order with stop-loss, target, and other features"""
        try:
            response = self.session.post(
                f'{self.base_url}/smart/order',
                json=order_details
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error placing order: {e}")
            return {}
    
    def analyze_portfolio_performance(self) -> Dict:
        """Analyze portfolio performance metrics"""
        holdings = self.get_portfolio_holdings()
        positions = self.get_portfolio_positions()
        
        analysis = {
            'total_holdings_value': 0,
            'total_positions_value': 0,
            'sector_allocation': {},
            'profit_loss': 0,
            'performance_metrics': {}
        }
        
        # Process holdings
        if holdings.get('status') == 'success':
            for holding in holdings.get('data', []):
                value = holding.get('holding_value', 0)
                analysis['total_holdings_value'] += value
        
        # Process positions
        if positions.get('status') == 'success':
            for position in positions.get('data', []):
                value = position.get('position_value', 0)
                analysis['total_positions_value'] += value
        
        analysis['total_portfolio_value'] = (
            analysis['total_holdings_value'] + analysis['total_positions_value']
        )
        
        return analysis
    
    def get_top_movers(self, exchange: str = 'NSE') -> List[Dict]:
        """Get top gainers and losers for market analysis"""
        # This would typically use a different endpoint for market movers
        # Implementation would depend on available API endpoints
        return []
    
    def create_investment_strategy(self, strategy_config: Dict) -> Dict:
        """Create and execute investment strategies"""
        # Example strategy implementation
        strategy_type = strategy_config.get('type', 'buy_and_hold')
        
        if strategy_type == 'buy_and_hold':
            return self._execute_buy_and_hold_strategy(strategy_config)
        elif strategy_type == 'swing_trading':
            return self._execute_swing_trading_strategy(strategy_config)
        else:
            return {'error': 'Unknown strategy type'}
    
    def _execute_buy_and_hold_strategy(self, config: Dict) -> Dict:
        """Execute buy and hold investment strategy"""
        scrip_codes = config.get('scrip_codes', [])
        allocation_percent = config.get('allocation_percent', 100)
        
        orders = []
        for code in scrip_codes:
            # Get current price
            ltp_data = self.get_ltp([code])
            if ltp_data.get('status') == 'success':
                current_price = ltp_data['data'][0].get('ltp', 0)
                
                order = {
                    "txn_type": "BUY",
                    "exchange": "NSE",
                    "segment": "EQUITY",
                    "product": "CNC",
                    "order_type": "MARKET",
                    "validity": "DAY",
                    "security_id": code,
                    "qty": self._calculate_quantity(config.get('capital', 10000), current_price, allocation_percent / len(scrip_codes))
                }
                orders.append(order)
        
        return {'orders': orders}
    
    def _execute_swing_trading_strategy(self, config: Dict) -> Dict:
        """Execute swing trading strategy with technical indicators"""
        # Implementation for swing trading with stop-loss and targets
        return {'message': 'Swing trading strategy implementation'}
    
    def _calculate_quantity(self, capital: float, price: float, allocation_percent: float) -> int:
        """Calculate order quantity based on capital allocation"""
        allocated_capital = capital * (allocation_percent / 100)
        return int(allocated_capital / price)
    
    def get_mutual_funds_data(self, mf_api_key: str = None) -> Dict:
        """
        Get mutual funds data using external API
        Note: IndStocks API doesn't support mutual funds, so we use external API
        """
        if not mf_api_key:
            print("Mutual fund API key required for MF data")
            return {}
        
        try:
            # Using mfapi.in or similar external service
            url = "https://api.mfapi.in/mf"
            headers = {'X-API-Key': mf_api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching mutual funds: {e}")
            return {}
    
    def get_mutual_fund_portfolio(self, folio_numbers: List[str], mf_api_key: str = None) -> Dict:
        """Get mutual fund portfolio from external service"""
        if not mf_api_key:
            return {'error': 'Mutual fund API key required'}
        
        portfolio_data = {}
        for folio in folio_numbers:
            try:
                url = f"https://api.mfapi.in/mf/{folio}"
                headers = {'X-API-Key': mf_api_key}
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                portfolio_data[folio] = response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching folio {folio}: {e}")
                portfolio_data[folio] = {'error': str(e)}
        
        return portfolio_data
    
    def generate_portfolio_report(self, include_mutual_funds: bool = False, mf_api_key: str = None) -> str:
        """Generate comprehensive portfolio report including mutual funds if requested"""
        analysis = self.analyze_portfolio_performance()
        holdings = self.get_portfolio_holdings()
        positions = self.get_portfolio_positions()
        
        report = f"""
=== INVESTMENT PORTFOLIO REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

STOCK PORTFOLIO SUMMARY:
- Total Stock Holdings Value: ₹{analysis['total_holdings_value']:,.2f}
- Total Stock Positions Value: ₹{analysis['total_positions_value']:,.2f}
- Total Stock Portfolio Value: ₹{analysis['total_portfolio_value']:,.2f}

STOCK HOLDINGS:
"""
        
        if holdings.get('status') == 'success':
            for holding in holdings.get('data', []):
                report += f"- {holding.get('symbol', 'N/A')}: {holding.get('quantity', 0)} shares @ ₹{holding.get('avg_price', 0):.2f}\n"
        
        report += "\nSTOCK POSITIONS:\n"
        if positions.get('status') == 'success':
            for position in positions.get('data', []):
                report += f"- {position.get('symbol', 'N/A')}: {position.get('quantity', 0)} shares @ ₹{position.get('avg_price', 0):.2f}\n"
        
        # Add mutual funds section if requested
        if include_mutual_funds and mf_api_key:
            mf_data = self.get_mutual_funds_data(mf_api_key)
            if mf_data:
                report += "\n=== MUTUAL FUNDS ===\n"
                report += "Note: Mutual fund data from external API (mfapi.in)\n"
                report += f"Total MF schemes tracked: {len(mf_data.get('data', []))}\n"
        
        return report


# Example Usage
def main():
    # Get access token from environment variable
    access_token = os.getenv('INDSTOCKS_TOKEN')
    if not access_token:
        print("Please set INDSTOCKS_TOKEN environment variable")
        return
    
    # Initialize investment manager
    investor = IndStocksInvestment(access_token)
    
    # Test connection
    profile = investor.get_user_profile()
    if profile.get('status') == 'success':
        print(f"✅ Connected! Welcome, {profile['data']['first_name']} {profile['data']['last_name']}")
    
    # Get portfolio overview
    analysis = investor.analyze_portfolio_performance()
    print(f"Portfolio Value: ₹{analysis['total_portfolio_value']:,.2f}")
    
    # Generate report
    report = investor.generate_portfolio_report()
    print(report)
    
    # Example investment strategy
    strategy_config = {
        'type': 'buy_and_hold',
        'scrip_codes': ['NSE_3045', 'NSE_500112'],  # Example stock codes
        'capital': 50000,
        'allocation_percent': 80
    }
    
    strategy_result = investor.create_investment_strategy(strategy_config)
    print("Strategy Orders:", strategy_result)


if __name__ == "__main__":
    main()
