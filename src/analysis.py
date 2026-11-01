"""Canonical KPIs, KRIs, descriptive tables, segmentation, and diagnostic tests."""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats


def _col(df, candidates):
    low={str(c).strip().lower():c for c in df.columns}
    for x in candidates:
        if x.lower() in low: return low[x.lower()]
    return None

def _numeric(df, candidates):
    c=_col(df,candidates)
    return pd.to_numeric(df[c],errors='coerce') if c else pd.Series(np.nan,index=df.index,dtype=float)

def _dates(df,candidates):
    c=_col(df,candidates)
    if not c: return pd.Series(pd.NaT,index=df.index,dtype='datetime64[ns]')
    return pd.to_datetime(df[c],errors='coerce',utc=True).dt.tz_convert(None)

def item_revenue(items: pd.DataFrame) -> pd.DataFrame:
    """Revenue per order = SUM(price) + SUM(freight_value), from order items."""
    x=items.copy(); oid=_col(x,['order_id']); price=_col(x,['price','item_price']); freight=_col(x,['freight_value','freight'])
    if not oid or not price or not freight:
        raise KeyError(f"items must contain order_id, price, freight_value. Found: {list(x.columns)}")
    x['_price']=pd.to_numeric(x[price],errors='coerce').fillna(0)
    x['_freight']=pd.to_numeric(x[freight],errors='coerce').fillna(0)
    x['_revenue']=x['_price']+x['_freight']
    x['_price']=x['_price']; x['_freight']=x['_freight']
    return x.groupby(oid).agg(revenue=('_revenue','sum'),price_sum=('_price','sum'),freight_sum=('_freight','sum'),item_count=(oid,'size'),items_revenue=('_revenue','sum')).reset_index().rename(columns={oid:'order_id'})

def prepare_orders(data: dict[str,pd.DataFrame]) -> pd.DataFrame:
    o=data['order_360'].copy(); oid=_col(o,['order_id'])
    if not oid: raise KeyError('order_360 has no order_id')
    if oid!='order_id': o=o.rename(columns={oid:'order_id'})
    o['purchase_dt']=_dates(o,['purchase_dt','order_purchase_timestamp','purchase_timestamp'])
    o['delivered_dt']=_dates(o,['delivered_dt','order_delivered_customer_date'])
    o['estimated_dt']=_dates(o,['estimated_dt','order_estimated_delivery_date'])
    o['carrier_dt']=_dates(o,['carrier_dt','order_delivered_carrier_date','carrier_date'])
    o['status']=o[_col(o,['order_status','status'])].astype('string').str.lower() if _col(o,['order_status','status']) else 'unknown'
    o['review_score']=_numeric(o,['review_score','average_review_score','avg_review_score'])
    o['customer_state_std']=o[_col(o,['customer_state','state'])].astype('string').str.upper() if _col(o,['customer_state','state']) else 'Unknown'
    # SQL formula is authoritative: order-item price plus freight.
    ir=item_revenue(data['items'])
    o=o.drop(columns=[c for c in ['revenue','price_sum','freight_sum','item_count'] if c in o.columns],errors='ignore')
    o=o.merge(ir,on='order_id',how='left',validate='one_to_one')
    o['revenue']=o['revenue'].fillna(0)
    # Use SQL delivery flag when present, with date-derived fallback for missing flags.
    provided=_numeric(o,['is_late'])
    from_dates=(o['delivered_dt'].notna() & o['estimated_dt'].notna() & (o['delivered_dt']>o['estimated_dt'])).astype(float)
    o['is_late_std']=provided.where(provided.notna(),from_dates)
    delivered_mask=o['status'].eq('delivered') | o['delivered_dt'].notna()
    o['is_delivered_std']=delivered_mask
    days=(o['delivered_dt']-o['purchase_dt']).dt.total_seconds()/86400
    o['delivery_days_std']=_numeric(o,['delivery_days']).where(_numeric(o,['delivery_days']).notna(),days)
    # Recalculate reliable delivery durations from timestamps when both exist.
    o.loc[o['delivered_dt'].notna() & o['purchase_dt'].notna(),'delivery_days_std']=days[o['delivered_dt'].notna() & o['purchase_dt'].notna()]
    o['on_time_std']=o['is_late_std'].eq(0).where(o['is_late_std'].notna())
    date_delay=(o['delivered_dt']-o['estimated_dt']).dt.total_seconds()/86400
    o['delay_days_std']=_numeric(o,['delay_days']).where(_numeric(o,['delay_days']).notna(), date_delay)
    return o

def build_kpis(data):
    o=prepare_orders(data); c=_customer_table(data,o)
    total_revenue=float(o['revenue'].sum()); n_orders=o['order_id'].nunique()
    order_customer_col=_col(o,['customer_unique_id'])
    customer_id=_col(c,['customer_unique_id','customer_id'])
    if order_customer_col:
        valid_customers=o.dropna(subset=[order_customer_col])
        unique_customers=int(valid_customers[order_customer_col].nunique())
        customer_order_counts=valid_customers.groupby(order_customer_col)['order_id'].nunique()
        repeat=float((customer_order_counts>=2).mean()*100) if len(customer_order_counts) else np.nan
    else:
        unique_customers=int(c[customer_id].nunique()) if customer_id else len(c)
        freq_col=_col(c,['n_orders','order_count'])
        repeat=float((pd.to_numeric(c[freq_col],errors='coerce')>=2).mean()*100) if freq_col and len(c) else np.nan
    reviewed=o['review_score'].dropna(); delivered=o.loc[o['is_delivered_std']]
    delivered_count=int(delivered['order_id'].nunique())
    late_known=delivered['is_late_std'].dropna()
    ontime=float((late_known==0).sum()/len(late_known)*100) if len(late_known) else np.nan
    late_rate=float((late_known==1).sum()/len(late_known)*100) if len(late_known) else np.nan
    seller_rev=_seller_table(data,o); top10=float(seller_rev.head(10)['revenue'].sum()/total_revenue*100) if total_revenue else np.nan
    sp_share=float(o.loc[o['customer_state_std'].eq('SP'),'revenue'].sum()/total_revenue*100) if total_revenue else np.nan
    mismatch=_numeric(o,['payment_mismatch']); mismatch_orders=int(o.loc[mismatch.fillna(0).astype(float)>0,'order_id'].nunique())
    cancelled=int(o.loc[o['status'].isin(['canceled','cancelled','unavailable']),'order_id'].nunique())
    monthly=build_monthly(data,o); mom=monthly['revenue_mom_growth_pct'].dropna(); latest_mom=float(mom.iloc[-1]) if len(mom) else np.nan
    rows=[
        ('Total revenue (BRL)','total_revenue',total_revenue,'BRL'),
        ('Orders','orders',int(n_orders),'orders'),
        ('Average order value (BRL)','average_order_value',total_revenue/n_orders if n_orders else np.nan,'BRL'),
        ('Unique customers','unique_customers',unique_customers,'customers'),
        ('Repeat-customer rate (%)','repeat_customer_rate',repeat,'%'),
        ('Average review score','average_review_score',float(reviewed.mean()) if len(reviewed) else np.nan,'score / 5'),
        ('Satisfaction (%)','satisfaction_pct',float(reviewed.ge(4).mean()*100) if len(reviewed) else np.nan,'%'),
        ('Average delivery days','average_delivery_days',float(delivered['delivery_days_std'].mean()) if delivered['delivery_days_std'].notna().any() else np.nan,'days'),
        ('On-time delivery (%)','on_time_delivery_pct',ontime,'%'),
        ('Top-10 seller share (%)','top10_seller_share',top10,'%'),
        ('Revenue growth MoM (%)','revenue_growth_mom_pct',latest_mom,'%'),
    ]
    return pd.DataFrame(rows,columns=['kpi','metric_id','python_value','unit'])

def build_kris(data):
    o=prepare_orders(data); total=o['order_id'].nunique(); delivered=o.loc[o['is_delivered_std']]; reviews=o['review_score'].dropna()
    known_delivery=delivered[delivered['is_late_std'].notna()]
    late_count=int(known_delivery.loc[known_delivery['is_late_std'].eq(1),'order_id'].nunique())
    low_rate=float(reviews.le(2).mean()*100) if len(reviews) else np.nan
    cancel=int(o.loc[o['status'].isin(['canceled','cancelled']),'order_id'].nunique()); unavailable=int(o.loc[o['status'].eq('unavailable'),'order_id'].nunique())
    seller_rev=_seller_table(data,o); revenue=float(o['revenue'].sum()); top10=float(seller_rev.head(10)['revenue'].sum()/revenue*100) if revenue else np.nan
    sp_share=float(o.loc[o['customer_state_std'].eq('SP'),'revenue'].sum()/revenue*100) if revenue else np.nan
    mismatch=_numeric(o,['payment_mismatch']); mismatch_count=int(o.loc[mismatch.fillna(0)>0,'order_id'].nunique())
    rows=[
      ('Late-delivery rate (%)','late_delivery_rate',late_count/(known_delivery['order_id'].nunique() or np.nan)*100,'%'),
      ('Share of 1–2 star reviews (%)','low_review_rate_1_2',low_rate,'%'),
      ('Canceled orders (%)','canceled_orders_pct',cancel/(total or np.nan)*100,'%'),
      ('Unavailable orders (%)','unavailable_orders_pct',unavailable/(total or np.nan)*100,'%'),
      ('Canceled + unavailable (%)','canceled_unavailable_pct',(cancel+unavailable)/(total or np.nan)*100,'%'),
      ('Top-10 seller revenue share (%)','top10_seller_share',top10,'%'),
      ('São Paulo revenue share (%)','sp_revenue_share',sp_share,'%'),
      ('Orders with payment mismatch','payment_mismatch_orders',mismatch_count,'orders'),
      ('Payment mismatch rate (%)','payment_mismatch_rate',mismatch_count/(total or np.nan)*100,'%'),
    ]
    return pd.DataFrame(rows,columns=['kri','metric_id','python_value','unit'])

def build_monthly(data, orders=None):
    o=orders if orders is not None else prepare_orders(data)
    d=o.loc[o['purchase_dt'].notna()].copy()
    if d.empty: return pd.DataFrame(columns=['month','revenue','orders','average_order_value','revenue_mom_growth_pct','revenue_yoy_growth_pct'])
    d['month']=d['purchase_dt'].dt.to_period('M').astype(str)
    m=d.groupby('month').agg(revenue=('revenue','sum'),orders=('order_id','nunique')).reset_index().sort_values('month')
    m['average_order_value']=m['revenue']/m['orders'].replace(0,np.nan)
    m['revenue_mom_growth_pct']=m['revenue'].pct_change()*100
    m['revenue_yoy_growth_pct']=m['revenue'].pct_change(12)*100
    return m

def _seller_table(data, orders=None):
    o=orders if orders is not None else prepare_orders(data); items=data['items'].copy(); products=data['products'].copy()
    sid=_col(items,['seller_id']); oid=_col(items,['order_id']); price=_col(items,['price']); freight=_col(items,['freight_value'])
    if not sid or not oid or not price: return pd.DataFrame(columns=['seller_id','revenue','items','orders','seller_state'])
    items['_rev']=pd.to_numeric(items[price],errors='coerce').fillna(0)+(pd.to_numeric(items[freight],errors='coerce').fillna(0) if freight else 0)
    s=items.groupby(sid).agg(revenue=('_rev','sum'),items=(oid,'size'),orders=(oid,'nunique')).reset_index().rename(columns={sid:'seller_id'})
    sellers=data.get('seller_360',pd.DataFrame()); sc=_col(sellers,['seller_id']); state=_col(sellers,['state','seller_state'])
    if sc and state: s=s.merge(sellers[[sc,state]].drop_duplicates(sc).rename(columns={sc:'seller_id',state:'seller_state'}),on='seller_id',how='left')
    return s.sort_values('revenue',ascending=False).reset_index(drop=True)

def build_categories(data, orders=None):
    items=data['items'].copy(); products=data['products'].copy(); oid=_col(items,['order_id']); pid=_col(items,['product_id']); price=_col(items,['price']); freight=_col(items,['freight_value']); ppid=_col(products,['product_id']); cat=_col(products,['category_en','product_category_name_english','product_category_name','category_name'])
    if not all([oid,pid,price,ppid,cat]): return pd.DataFrame(columns=['category','revenue','orders','contribution_pct','cumulative_pct'])
    items['_rev']=pd.to_numeric(items[price],errors='coerce').fillna(0)+(pd.to_numeric(items[freight],errors='coerce').fillna(0) if freight else 0)
    j=items.merge(products[[ppid,cat]].drop_duplicates(ppid),left_on=pid,right_on=ppid,how='left')
    g=j.groupby(cat,dropna=False).agg(revenue=('_rev','sum'),orders=(oid,'nunique')).reset_index().rename(columns={cat:'category'}).sort_values('revenue',ascending=False)
    g['contribution_pct']=g['revenue']/g['revenue'].sum()*100 if g['revenue'].sum() else np.nan
    g['cumulative_pct']=g['contribution_pct'].cumsum()
    return g

def build_states(data, orders=None):
    o=orders if orders is not None else prepare_orders(data)
    g=o.groupby('customer_state_std',dropna=False).agg(revenue=('revenue','sum'),orders=('order_id','nunique'),avg_delivery_days=('delivery_days_std','mean'),satisfaction_pct=('review_score',lambda s:s.dropna().ge(4).mean()*100 if s.notna().any() else np.nan)).reset_index().rename(columns={'customer_state_std':'state'})
    g['average_order_value']=g['revenue']/g['orders'].replace(0,np.nan)
    return g.sort_values('revenue',ascending=False)

def build_payment_mix(data):
    p=data.get('payments',pd.DataFrame()).copy()
    types=[('Credit card','credit_card_amt'),('Debit card','debit_card_amt'),('Boleto','boleto_amt'),('Voucher','voucher_amt'),('Not defined','not_defined_amt')]
    rows=[]; n_orders=len(p)
    for label,col in types:
        c=_col(p,[col])
        if c:
            values=pd.to_numeric(p[c],errors='coerce').fillna(0)
            rows.append({'payment_type':label,'payment_value':float(values.sum()),'orders_using_type':int((values>0).sum()),'mean_value_when_used':float(values[values>0].mean()) if (values>0).any() else np.nan})
    out=pd.DataFrame(rows)
    if not out.empty:
        out['value_share_pct']=out['payment_value']/out['payment_value'].sum()*100 if out['payment_value'].sum() else np.nan
        out['order_share_pct']=out['orders_using_type']/n_orders*100 if n_orders else np.nan
    return out

def build_daily_patterns(data, orders=None):
    o=orders if orders is not None else prepare_orders(data); d=o[o['purchase_dt'].notna()].copy()
    d['weekday']=d['purchase_dt'].dt.day_name(); d['weekday_num']=d['purchase_dt'].dt.dayofweek; d['hour']=d['purchase_dt'].dt.hour
    weekdays=d.groupby(['weekday_num','weekday']).agg(orders=('order_id','nunique'),revenue=('revenue','sum')).reset_index().sort_values('weekday_num')
    hours=d.groupby('hour').agg(orders=('order_id','nunique'),revenue=('revenue','sum')).reset_index()
    return weekdays,hours

def _customer_table(data, orders):
    c=data.get('customer_360',pd.DataFrame()).copy()
    if not c.empty:
        # Normalize expected names but use order rollup for authoritative frequency/revenue when possible.
        idc=_col(c,['customer_unique_id','customer_id'])
        if idc and idc!='customer_unique_id': c=c.rename(columns={idc:'customer_unique_id'})
        if 'customer_unique_id' in c.columns:
            n=_col(c,['n_orders','order_count']); rev=_col(c,['revenue','total_revenue']); rec=_col(c,['recency_days']); state=_col(c,['state','customer_state'])
            if n and n!='n_orders': c=c.rename(columns={n:'n_orders'})
            if rev and rev!='revenue': c=c.rename(columns={rev:'revenue'})
            if rec and rec!='recency_days': c=c.rename(columns={rec:'recency_days'})
            if state and state!='state': c=c.rename(columns={state:'state'})
            return c
    custcol=_col(orders,['customer_unique_id'])
    if not custcol: return pd.DataFrame(columns=['customer_unique_id','n_orders','revenue','recency_days','state','first_order_dt','last_order_dt','avg_review_score','is_repeat'])
    c=orders.groupby(custcol).agg(n_orders=('order_id','nunique'),revenue=('revenue','sum'),first_order_dt=('purchase_dt','min'),last_order_dt=('purchase_dt','max'),avg_review_score=('review_score','mean'),state=('customer_state_std','last')).reset_index().rename(columns={custcol:'customer_unique_id'})
    c['recency_days']=(orders['purchase_dt'].max()-c['last_order_dt']).dt.days; c['is_repeat']=(c['n_orders']>=2).astype(int); return c

def build_customer_segments(data, orders=None):
    o=orders if orders is not None else prepare_orders(data); c=_customer_table(data,o).copy()
    if c.empty: return c, pd.DataFrame(), pd.DataFrame()
    for col in ['revenue','n_orders','recency_days']:
        if col not in c: c[col]=np.nan
        c[col]=pd.to_numeric(c[col],errors='coerce')
    c['value_segment']=pd.cut(c['revenue'].rank(pct=True,method='average'),[0,1/3,2/3,1],labels=['Low','Medium','High'],include_lowest=True).astype('string')
    # RFM scores 1-3; lower recency days means a stronger recency score.
    c['R_score']=np.ceil(c['recency_days'].rank(pct=True,ascending=False,method='average')*3).clip(1,3)
    c['F_score']=np.ceil(c['n_orders'].rank(pct=True,ascending=True,method='average')*3).clip(1,3)
    c['M_score']=np.ceil(c['revenue'].rank(pct=True,ascending=True,method='average')*3).clip(1,3)
    c[['R_score','F_score','M_score']]=c[['R_score','F_score','M_score']].fillna(1).astype(int)
    c['RFM_total']=c[['R_score','F_score','M_score']].sum(axis=1)
    c['rfm_segment']=np.select([c.RFM_total>=8,c.RFM_total>=7,c.RFM_total>=5],['Platinum','Gold','Silver'],default='Standard')
    # Compare most recent six months with the preceding six months based on latest observed purchase date.
    maxdate=o['purchase_dt'].max(); cur_start=maxdate-pd.DateOffset(months=6); prev_start=maxdate-pd.DateOffset(months=12)
    customer_col=_col(o,['customer_unique_id'])
    if customer_col and pd.notna(maxdate):
        spends=o[o['purchase_dt'].between(cur_start,maxdate)].groupby(customer_col)['revenue'].sum().rename('current_spend')
        prev=o[o['purchase_dt'].between(prev_start,cur_start,inclusive='left')].groupby(customer_col)['revenue'].sum().rename('previous_spend')
        loy=c[['customer_unique_id','revenue','first_order_dt']].copy() if 'first_order_dt' in c else c[['customer_unique_id','revenue']].copy()
        loy=loy.merge(spends,left_on='customer_unique_id',right_index=True,how='left').merge(prev,left_on='customer_unique_id',right_index=True,how='left').fillna({'current_spend':0,'previous_spend':0})
        if 'first_order_dt' not in loy: loy['first_order_dt']=pd.NaT
        cur=loy.current_spend; old=loy.previous_spend
        new=(cur>0)&(old==0)&(pd.to_datetime(loy.first_order_dt,errors='coerce')>=cur_start)
        dormant=(cur==0)&(pd.to_numeric(loy.revenue,errors='coerce').fillna(0)>0)
        upward=((cur>old*1.1)&(old>0)) | ((cur>0)&(old==0)&(pd.to_numeric(loy.revenue,errors='coerce').fillna(0)>0)&(~new))
        downward=(cur<old*0.9)&(cur>0)&(old>0)
        loy['loyalty_segment']=np.select([new,dormant,upward,downward],['New','Dormant','Upward migrator','Downward migrator'],default='Consistent')
        loy['current_period_start']=cur_start; loy['previous_period_start']=prev_start; loy['period_end']=maxdate
    else:
        loy=pd.DataFrame(columns=['customer_unique_id','current_spend','previous_spend','loyalty_segment'])
    value_summary=c.groupby('value_segment',dropna=False).agg(customers=('customer_unique_id','nunique'),revenue=('revenue','sum'),avg_revenue=('revenue','mean')).reset_index()
    rfm_summary=c.groupby('rfm_segment',dropna=False).agg(customers=('customer_unique_id','nunique'),revenue=('revenue','sum'),avg_orders=('n_orders','mean')).reset_index()
    return c,value_summary,loy

def _chi_square(group, target, min_group=1):
    temp=pd.DataFrame({'group':group,'target':target}).dropna()
    counts=temp.groupby('group').size(); keep=counts[counts>=min_group].index
    temp=temp[temp.group.isin(keep)]
    ct=pd.crosstab(temp['group'],temp['target'])
    if ct.shape[0]<2 or ct.shape[1]<2: return np.nan,np.nan
    try:
        chi,p,_,_=stats.chi2_contingency(ct)
        return float(chi),float(p)
    except ValueError: return np.nan,np.nan

def build_diagnostics(data, orders=None):
    """Build diagnostic summaries, hypothesis tests and delay/cancellation breakdowns."""
    o = orders if orders is not None else prepare_orders(data)
    delivered = o[o['is_delivered_std']].copy()
    known_late = delivered['is_late_std'].notna()
    late_scores = delivered.loc[known_late & delivered['is_late_std'].eq(1), 'review_score'].dropna()
    ontime_scores = delivered.loc[known_late & delivered['is_late_std'].eq(0), 'review_score'].dropna()
    if len(late_scores) > 1 and len(ontime_scores) > 1:
        t_stat, t_p = stats.ttest_ind(late_scores, ontime_scores, equal_var=False, nan_policy='omit')
    else:
        t_stat, t_p = np.nan, np.nan
    late_review = pd.DataFrame([
        {'group': 'Late', 'orders': len(late_scores), 'average_review_score': late_scores.mean()},
        {'group': 'On time', 'orders': len(ontime_scores), 'average_review_score': ontime_scores.mean()},
    ])

    items = data['items'].copy()
    products = data['products'].copy()
    item_order_col = _col(items, ['order_id'])
    item_product_col = _col(items, ['product_id'])
    seller_col = _col(items, ['seller_id'])
    price_col = _col(items, ['price'])
    freight_col = _col(items, ['freight_value'])
    product_id_col = _col(products, ['product_id'])
    category_col = _col(products, ['category_en', 'product_category_name_english', 'product_category_name', 'category_name'])

    order_review = o[['order_id', 'review_score', 'is_late_std', 'status', 'purchase_dt', 'customer_state_std', 'revenue', 'delivery_days_std', 'carrier_dt', 'estimated_dt']].copy()
    order_review['low_1_2'] = order_review['review_score'].le(2).astype(int)
    order_review['cancel_flag'] = order_review['status'].isin(['canceled', 'cancelled', 'unavailable']).astype(int)

    if item_order_col and item_product_col and product_id_col and category_col:
        joined_items = items.merge(
            products[[product_id_col, category_col]].drop_duplicates(product_id_col),
            left_on=item_product_col, right_on=product_id_col, how='left'
        )
    else:
        joined_items = items.copy()
        joined_items['_category'] = 'Unknown'
        category_col = '_category'

    jc = joined_items.merge(
        order_review[['order_id', 'review_score', 'low_1_2', 'cancel_flag', 'is_late_std', 'purchase_dt']],
        left_on=item_order_col, right_on='order_id', how='left'
    ) if item_order_col and category_col else pd.DataFrame()

    if not jc.empty:
        category_low = jc.groupby(category_col, dropna=False).agg(
            items=(item_order_col, 'size'),
            orders=('order_id', 'nunique'),
            low_review_rate_pct=('low_1_2', lambda x: x.mean() * 100),
            late_rate_pct=('is_late_std', lambda x: pd.to_numeric(x, errors='coerce').mean() * 100),
            cancel_rate_pct=('cancel_flag', lambda x: x.mean() * 100),
            average_review_score=('review_score', 'mean'),
        ).reset_index().rename(columns={category_col: 'category'})
        category_late_counts = jc.loc[jc['is_late_std'].eq(1)].groupby(category_col)['order_id'].nunique()
        category_low['late_orders'] = category_low['category'].map(category_late_counts).fillna(0).astype(int)
        category_low = category_low.sort_values('low_review_rate_pct', ascending=False)
        category_pareto = category_low.sort_values('late_orders', ascending=False).copy()
        total_late_category = category_pareto['late_orders'].sum()
        category_pareto['cumulative_late_share_pct'] = category_pareto['late_orders'].cumsum() / total_late_category * 100 if total_late_category else np.nan
    else:
        category_low = pd.DataFrame()
        category_pareto = pd.DataFrame()

    if seller_col and item_order_col:
        js = items.merge(
            order_review[['order_id', 'review_score', 'low_1_2', 'cancel_flag', 'is_late_std']],
            left_on=item_order_col, right_on='order_id', how='left'
        )
        seller_low = js.groupby(seller_col).agg(
            items=(item_order_col, 'size'), orders=('order_id', 'nunique'),
            low_review_rate_pct=('low_1_2', lambda x: x.mean() * 100),
            late_rate_pct=('is_late_std', lambda x: pd.to_numeric(x, errors='coerce').mean() * 100),
            cancel_rate_pct=('cancel_flag', lambda x: x.mean() * 100),
            average_review_score=('review_score', 'mean'),
        ).reset_index().rename(columns={seller_col: 'seller_id'})
        seller_late_counts = js.loc[js['is_late_std'].eq(1)].groupby(seller_col)['order_id'].nunique()
        seller_low['late_orders'] = seller_low['seller_id'].map(seller_late_counts).fillna(0).astype(int)
        seller_delays = seller_low.sort_values('late_rate_pct', ascending=False)
        seller_pareto = seller_low.sort_values('late_orders', ascending=False).copy()
        total_seller_late = seller_pareto['late_orders'].sum()
        seller_pareto['cumulative_late_share_pct'] = seller_pareto['late_orders'].cumsum() / total_seller_late * 100 if total_seller_late else np.nan
    else:
        js = pd.DataFrame()
        seller_low = pd.DataFrame()
        seller_delays = pd.DataFrame()
        seller_pareto = pd.DataFrame()

    state_low = order_review.groupby('customer_state_std').agg(
        orders=('order_id', 'nunique'),
        low_review_rate_pct=('low_1_2', lambda x: x.mean() * 100),
        late_rate_pct=('is_late_std', lambda x: pd.to_numeric(x, errors='coerce').mean() * 100),
        average_review_score=('review_score', 'mean'),
        avg_delivery_days=('delivery_days_std', 'mean'),
    ).reset_index().rename(columns={'customer_state_std': 'state'}).sort_values('low_review_rate_pct', ascending=False)

    # Freight ratio analysis at order level; zero-price orders have no defined ratio.
    if item_order_col and price_col:
        items['_price'] = pd.to_numeric(items[price_col], errors='coerce').fillna(0)
        items['_freight'] = pd.to_numeric(items[freight_col], errors='coerce').fillna(0) if freight_col else 0
        fr = items.groupby(item_order_col).agg(price=('_price', 'sum'), freight=('_freight', 'sum')).reset_index().rename(columns={item_order_col: 'order_id'})
        fr['freight_ratio'] = fr['freight'] / fr['price'].replace(0, np.nan)
        fr = fr.merge(order_review[['order_id', 'review_score', 'low_1_2']], on='order_id', how='left')
        valid_fr = fr[['freight_ratio', 'review_score']].dropna()
        corr = valid_fr.corr(method='spearman').iloc[0, 1] if len(valid_fr) > 2 else np.nan
        fr['freight_band'] = pd.cut(fr['freight_ratio'], bins=[-np.inf, .1, .25, .5, 1, np.inf], labels=['≤10%', '10–25%', '25–50%', '50–100%', '>100%'])
        freight_bands = fr.groupby('freight_band', observed=False).agg(
            orders=('order_id', 'nunique'), average_review_score=('review_score', 'mean'),
            low_review_rate_pct=('low_1_2', lambda x: x.mean() * 100)
        ).reset_index()
    else:
        corr = np.nan
        freight_bands = pd.DataFrame()

    cancel_month = o.groupby(o['purchase_dt'].dt.to_period('M').astype(str)).agg(
        orders=('order_id', 'nunique'),
        cancel_rate_pct=('status', lambda x: x.isin(['canceled', 'cancelled', 'unavailable']).mean() * 100),
    ).reset_index().rename(columns={'purchase_dt': 'month'})

    # Carrier pickup delay: order carrier timestamp after item shipping_limit_date.
    pickup_seller = pd.DataFrame()
    pickup_category = pd.DataFrame()
    if item_order_col and 'shipping_limit_date' in items.columns and order_review['carrier_dt'].notna().any():
        pickup = joined_items.copy()
        pickup['shipping_limit_dt'] = pd.to_datetime(pickup['shipping_limit_date'], errors='coerce', utc=True).dt.tz_convert(None)
        pickup = pickup.merge(order_review[['order_id', 'carrier_dt']], left_on=item_order_col, right_on='order_id', how='left')
        pickup['carrier_after_shipping_limit'] = (pickup['carrier_dt'].notna() & pickup['shipping_limit_dt'].notna() & (pickup['carrier_dt'] > pickup['shipping_limit_dt'])).astype(int)
        if seller_col:
            pickup_seller = pickup.groupby(seller_col).agg(items=(item_order_col, 'size'), late_pickup_rate_pct=('carrier_after_shipping_limit', lambda x: x.mean() * 100), late_pickup_items=('carrier_after_shipping_limit', 'sum')).reset_index().rename(columns={seller_col: 'seller_id'}).sort_values('late_pickup_rate_pct', ascending=False)
        if category_col in pickup.columns:
            pickup_category = pickup.groupby(category_col, dropna=False).agg(items=(item_order_col, 'size'), late_pickup_rate_pct=('carrier_after_shipping_limit', lambda x: x.mean() * 100), late_pickup_items=('carrier_after_shipping_limit', 'sum')).reset_index().rename(columns={category_col: 'category'}).sort_values('late_pickup_rate_pct', ascending=False)

    def test_from_frame(frame, group_col, target_col, min_group=20):
        if frame.empty or group_col not in frame.columns or target_col not in frame.columns:
            return np.nan, np.nan
        return _chi_square(frame[group_col], frame[target_col], min_group=min_group)

    chi_cat, p_cat = test_from_frame(jc, category_col, 'low_1_2') if not jc.empty else (np.nan, np.nan)
    chi_seller, p_seller = test_from_frame(js, seller_col, 'low_1_2') if not js.empty and seller_col else (np.nan, np.nan)
    chi_state, p_state = _chi_square(order_review['customer_state_std'], order_review['low_1_2'], min_group=20)
    chi_cat_cancel, p_cat_cancel = test_from_frame(jc, category_col, 'cancel_flag') if not jc.empty else (np.nan, np.nan)
    chi_seller_cancel, p_seller_cancel = test_from_frame(js, seller_col, 'cancel_flag') if not js.empty and seller_col else (np.nan, np.nan)

    test_results = pd.DataFrame([
        {'test': 'Welch t-test: review score, late vs on time', 'statistic': float(t_stat) if pd.notna(t_stat) else np.nan, 'p_value': float(t_p) if pd.notna(t_p) else np.nan, 'interpretation': 'Compares mean review scores in delivered orders with known late status.'},
        {'test': 'Spearman correlation: freight ratio vs review score', 'statistic': float(corr) if pd.notna(corr) else np.nan, 'p_value': np.nan, 'interpretation': 'Association only; correlation is not causation.'},
        {'test': 'Chi-square: category vs 1–2 star review', 'statistic': chi_cat, 'p_value': p_cat, 'interpretation': 'Association between category and low-review flag; item-level exposure.'},
        {'test': 'Chi-square: seller vs 1–2 star review', 'statistic': chi_seller, 'p_value': p_seller, 'interpretation': 'Association between seller and low-review flag; item-level exposure.'},
        {'test': 'Chi-square: state vs 1–2 star review', 'statistic': chi_state, 'p_value': p_state, 'interpretation': 'Association between state and the low-review indicator.'},
        {'test': 'Chi-square: category vs canceled/unavailable', 'statistic': chi_cat_cancel, 'p_value': p_cat_cancel, 'interpretation': 'Association between category and cancellation/unavailability; item-level exposure.'},
        {'test': 'Chi-square: seller vs canceled/unavailable', 'statistic': chi_seller_cancel, 'p_value': p_seller_cancel, 'interpretation': 'Association between seller and cancellation/unavailability; item-level exposure.'},
    ])
    return {
        'late_review': late_review, 'category_diagnostics': category_low,
        'category_late_pareto': category_pareto, 'seller_diagnostics': seller_low,
        'seller_delays': seller_delays, 'seller_late_pareto': seller_pareto,
        'state_diagnostics': state_low, 'freight_bands': freight_bands,
        'test_results': test_results, 'cancel_by_month': cancel_month,
        'carrier_pickup_by_seller': pickup_seller, 'carrier_pickup_by_category': pickup_category,
        'late_ttest_stat': float(t_stat) if pd.notna(t_stat) else np.nan,
        'late_ttest_pvalue': float(t_p) if pd.notna(t_p) else np.nan,
        'freight_spearman': float(corr) if pd.notna(corr) else np.nan,
    }

def build_dashboard_tables(data):
    o=prepare_orders(data); kpis=build_kpis(data); kris=build_kris(data); monthly=build_monthly(data,o); categories=build_categories(data,o); states=build_states(data,o); sellers=_seller_table(data,o); weekdays,hours=build_daily_patterns(data,o); customers,value_summary,loyalty=build_customer_segments(data,o); payments=build_payment_mix(data)
    reviews=o['review_score'].dropna().round().astype(int).value_counts().reindex([1,2,3,4,5],fill_value=0).rename_axis('review_score').reset_index(name='orders')
    delivery=o.loc[o['is_delivered_std']]
    late_values=delivery['is_late_std'].dropna()
    late_vs=pd.DataFrame({'delivery_status':['On time','Late'],'orders':[int((late_values==0).sum()),int((late_values==1).sum())]})
    bands=pd.cut(delivery['delivery_days_std'],bins=[-np.inf,3,7,14,21,np.inf],labels=['0–3 days','4–7 days','8–14 days','15–21 days','22+ days']).value_counts(sort=False).rename_axis('delivery_band').reset_index(name='orders')
    diagnostics=build_diagnostics(data,o)
    out={'kpis':kpis,'kris':kris,'monthly':monthly,'categories':categories,'states':states,'sellers':sellers,'weekday_patterns':weekdays,'hour_patterns':hours,'review_distribution':reviews,'late_vs_ontime':late_vs,'delay_bands':bands,'payment_mix':payments,'customer_segments':value_summary,'rfm_segments':customers.groupby('rfm_segment').agg(customers=('customer_unique_id','nunique'),revenue=('revenue','sum'),avg_orders=('n_orders','mean')).reset_index(),'loyalty_segments':loyalty,'cancel_by_month':diagnostics['cancel_by_month']}
    out.update({f'diag_{k}':v for k,v in diagnostics.items() if isinstance(v,pd.DataFrame)})
    return out
