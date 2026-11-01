"""Plotly chart helpers. These functions match the columns emitted by analysis.py."""
from __future__ import annotations
import pandas as pd
import plotly.express as px


def empty_chart(title, message='No data available for this selection.'):
    return px.scatter(title=f'{title} — {message}')

def chart(df,x,y,title,kind='bar',color=None):
    if df is None or df.empty or x not in df.columns or y not in df.columns: return empty_chart(title)
    d=df.copy(); d[y]=pd.to_numeric(d[y],errors='coerce'); d=d.dropna(subset=[y])
    if d.empty: return empty_chart(title)
    if kind=='line': fig=px.line(d,x=x,y=y,title=title,markers=True,color=color)
    elif kind=='area': fig=px.area(d,x=x,y=y,title=title,color=color)
    elif kind=='pie':
        d=d[d[y]>=0]
        if d.empty or d[y].sum()<=0: return empty_chart(title)
        fig=px.pie(d,names=x,values=y,title=title,hole=.42)
    elif kind=='scatter': fig=px.scatter(d,x=x,y=y,title=title,color=color)
    else: fig=px.bar(d,x=x,y=y,title=title,color=color)
    fig.update_layout(title_x=.02,margin=dict(l=20,r=20,t=60,b=30),legend_title_text='')
    return fig

def monthly_revenue_chart(df): return chart(df,'month','revenue','Monthly Revenue (BRL)','line')
def monthly_orders_chart(df): return chart(df,'month','orders','Orders by Month','bar')
def monthly_growth_chart(df): return chart(df,'month','revenue_mom_growth_pct','Month-over-Month Revenue Growth (%)','bar')
def category_revenue_chart(df): return chart(df.head(10),'category','revenue','Top 10 Categories by Revenue','bar')
def category_pareto_chart(df):
    if df is None or df.empty: return empty_chart('Category Pareto')
    d=df.head(15).copy(); fig=px.bar(d,x='category',y='revenue',title='Category Revenue — Pareto View')
    fig.add_scatter(x=d['category'],y=d['cumulative_pct'],name='Cumulative revenue share (%)',yaxis='y2',mode='lines+markers')
    fig.update_layout(yaxis2=dict(title='Cumulative share (%)',overlaying='y',side='right',range=[0,100]))
    return fig

def state_revenue_chart(df): return chart(df.head(27),'state','revenue','Revenue by Customer State','bar')
def review_distribution_chart(df): return chart(df,'review_score','orders','Order-Level Review Score Distribution','bar')
def delivery_status_chart(df): return chart(df,'delivery_status','orders','On-Time vs Late Deliveries','pie')
def delivery_bands_chart(df): return chart(df,'delivery_band','orders','Orders by Delivery Duration','bar')
def delivery_days_state_chart(df): return chart(df,'state','avg_delivery_days','Average Delivery Days by State','bar')
def payment_mix_chart(df): return chart(df,'payment_type','payment_value','Payment Value Mix','pie')
def value_segment_chart(df): return chart(df,'value_segment','customers','Customers by Revenue Segment','bar')
def rfm_chart(df): return chart(df,'rfm_segment','customers','Customers by RFM Segment','bar')
def loyalty_chart(df): return chart(df,'loyalty_segment','current_spend','Customer Spend by Loyalty Segment','bar')
def weekday_chart(df): return chart(df,'weekday','orders','Orders by Weekday','bar')
def hour_chart(df): return chart(df,'hour','orders','Orders by Purchase Hour','bar')
def seller_chart(df): return chart(df.head(15),'seller_id','revenue','Top 15 Sellers by Revenue','bar')
def freight_band_chart(df): return chart(df,'freight_band','average_review_score','Average Review by Freight-to-Price Band','bar')
def cancel_month_chart(df): return chart(df,'month','cancel_rate_pct','Canceled/Unavailable Rate by Month','line')
def low_review_category_chart(df): return chart(df.head(15),'category','low_review_rate_pct','1–2 Star Review Rate by Category','bar')
def seller_delay_chart(df): return chart(df.head(15),'seller_id','late_rate_pct','Late Delivery Rate by Seller','bar')

# Compatibility aliases from earlier files.
plot_monthly_revenue=monthly_revenue_chart
plot_monthly_orders=monthly_orders_chart
plot_category_revenue=category_revenue_chart
plot_state_revenue=state_revenue_chart
plot_review_distribution=review_distribution_chart
plot_delivery_status=delivery_status_chart
plot_delivery_bands=delivery_bands_chart
plot_delivery_days_by_state=delivery_days_state_chart
plot_payment_mix=payment_mix_chart


# Approximate Brazilian state centroids for a geographic revenue overview.
# These are display centroids, not customer/seller coordinates or distance measures.
BR_STATE_CENTROIDS = {
 'AC':(-9.0,-70.0),'AL':(-9.6,-36.6),'AP':(1.4,-51.8),'AM':(-3.5,-64.5),'BA':(-12.5,-41.7),
 'CE':(-5.2,-39.5),'DF':(-15.8,-47.9),'ES':(-19.5,-40.6),'GO':(-16.0,-49.5),'MA':(-5.0,-45.0),
 'MT':(-12.7,-55.4),'MS':(-20.5,-54.5),'MG':(-18.5,-44.5),'PA':(-3.8,-52.5),'PB':(-7.1,-36.5),
 'PR':(-24.7,-51.5),'PE':(-8.3,-37.8),'PI':(-7.0,-42.5),'RJ':(-22.3,-42.7),'RN':(-5.8,-36.5),
 'RS':(-30.0,-53.0),'RO':(-10.8,-63.0),'RR':(2.0,-61.5),'SC':(-27.3,-50.5),'SP':(-22.2,-48.8),
 'SE':(-10.6,-37.4),'TO':(-10.2,-48.3)
}

def state_bubble_map_chart(df):
    if df is None or df.empty or 'state' not in df.columns or 'revenue' not in df.columns:
        return empty_chart('Revenue by State Map')
    d=df.copy(); d['state']=d['state'].astype(str).str.upper(); d['revenue']=pd.to_numeric(d['revenue'],errors='coerce')
    d['lat']=d['state'].map({k:v[0] for k,v in BR_STATE_CENTROIDS.items()}); d['lon']=d['state'].map({k:v[1] for k,v in BR_STATE_CENTROIDS.items()})
    d=d.dropna(subset=['lat','lon','revenue'])
    if d.empty: return empty_chart('Revenue by State Map')
    fig=px.scatter_geo(d,lat='lat',lon='lon',size='revenue',color='revenue',hover_name='state',hover_data={'revenue':':,.0f','orders':True,'lat':False,'lon':False},scope='south america',projection='mercator',title='Revenue by State (approximate centroid bubble map)',size_max=38)
    fig.update_geos(fitbounds='locations',visible=True)
    fig.update_layout(title_x=.02,margin=dict(l=10,r=10,t=60,b=20))
    return fig

def category_delay_chart(df):
    return chart(df.head(15),'category','late_rate_pct','Late Delivery Rate by Category (%)','bar')


def _late_pareto(df, group_col, title):
    if df is None or df.empty or group_col not in df.columns or 'late_orders' not in df.columns:
        return empty_chart(title)
    d=df.sort_values('late_orders',ascending=False).head(15).copy()
    d['cumulative_late_share_pct']=d['late_orders'].cumsum()/d['late_orders'].sum()*100 if d['late_orders'].sum() else 0
    fig=px.bar(d,x=group_col,y='late_orders',title=title)
    fig.add_scatter(x=d[group_col],y=d['cumulative_late_share_pct'],name='Cumulative share (%)',mode='lines+markers',yaxis='y2')
    fig.update_layout(yaxis2=dict(title='Cumulative late-order share (%)',overlaying='y',side='right',range=[0,100]),title_x=.02,margin=dict(l=20,r=20,t=60,b=30))
    return fig

def seller_late_pareto_chart(df): return _late_pareto(df,'seller_id','Late Orders by Seller — Pareto')
def category_late_pareto_chart(df): return _late_pareto(df,'category','Late Orders by Category — Pareto')
def carrier_pickup_seller_chart(df): return chart(df.head(15),'seller_id','late_pickup_rate_pct','Carrier Pickup After Shipping Limit by Seller (%)','bar')
def carrier_pickup_category_chart(df): return chart(df.head(15),'category','late_pickup_rate_pct','Carrier Pickup After Shipping Limit by Category (%)','bar')


def monthly_aov_chart(df): return chart(df,'month','average_order_value','Monthly Average Order Value (BRL)','line')

def review_box_by_delivery_chart(df):
    if df is None or df.empty or 'delivery_timing' not in df.columns or 'review_score' not in df.columns: return empty_chart('Review Score by Delivery Timing')
    return px.box(df,x='delivery_timing',y='review_score',points='outliers',title='Review Score by Delivery Timing')
