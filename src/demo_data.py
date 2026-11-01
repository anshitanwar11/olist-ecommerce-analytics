"""Deterministic synthetic data so the app can be explored before extracts are copied in.

This is not real Olist data and must never be reported as real project results.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def make_demo_data(n_orders: int = 2600, seed: int = 42) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    n_customers = max(500, int(n_orders * 0.72))
    n_sellers = 140
    n_products = 280
    states = np.array(["SP","RJ","MG","RS","PR","SC","BA","DF","GO","PE","CE","ES","MT","MS","PA","PB","RN","AL","PI","MA","SE","TO","RO","AM","AC","AP","RR"])
    categories = np.array(["bed_bath_table","health_beauty","sports_leisure","furniture_decor","computer_accessories","housewares","watches_gifts","telephony","toys","auto","garden_tools","cool_stuff","perfumery","fashion_bags_accessories","baby"])
    purchase = pd.to_datetime(rng.integers(pd.Timestamp('2017-01-01').value // 10**9, pd.Timestamp('2018-09-01').value // 10**9, n_orders), unit='s')
    order_ids = np.array([f"DEMO{v:07d}" for v in range(1, n_orders+1)])
    cust_idx = rng.integers(0, n_customers, n_orders)
    customer_ids = np.array([f"CUST{v:06d}" for v in cust_idx])
    customer_states_by_id = rng.choice(states, n_customers, p=None)
    customer_state = customer_states_by_id[cust_idx]
    statuses = rng.choice(["delivered","canceled","unavailable","invoiced","shipped"], n_orders, p=[0.958,0.014,0.003,0.008,0.017])
    n_items = rng.choice([1,2,3,4], n_orders, p=[0.65,0.24,0.08,0.03])
    rows=[]
    products = pd.DataFrame({
        'product_id':[f'P{i:05d}' for i in range(n_products)],
        'category_pt':categories[rng.integers(0,len(categories),n_products)],
        'category_en':categories[rng.integers(0,len(categories),n_products)],
        'name_length':rng.integers(10,70,n_products),
        'description_length':rng.integers(50,2500,n_products),
        'photos_qty':rng.integers(1,8,n_products),
        'weight_g':rng.integers(100,20000,n_products),
        'weight_issue':0,
        'volume_cm3':rng.integers(100,100000,n_products),
    })
    seller_ids=np.array([f'SELL{i:04d}' for i in range(n_sellers)])
    seller_states=rng.choice(states,n_sellers)
    seller_cities=np.array([f'Seller City {i%80+1}' for i in range(n_sellers)])
    for i, oid in enumerate(order_ids):
        for j in range(int(n_items[i])):
            pid=int(rng.integers(0,n_products)); sid=int(rng.integers(0,n_sellers))
            price=float(np.clip(rng.lognormal(4.25,0.75),8,1800))
            freight=float(np.clip(price*rng.uniform(0.04,0.35),5,180))
            rows.append((oid,j+1,products.loc[pid,'product_id'],seller_ids[sid],purchase[i]+pd.Timedelta(days=int(rng.integers(1,3))),price,freight,sid))
    items=pd.DataFrame(rows,columns=['order_id','order_item_id','product_id','seller_id','shipping_limit_date','price','freight_value','_seller_index'])
    # Order totals from items.
    item_agg=items.groupby('order_id').agg(price_sum=('price','sum'),freight_sum=('freight_value','sum'),n_items=('order_item_id','size'),n_sellers=('seller_id','nunique')).reindex(order_ids).reset_index(names='order_id')
    price_sum=item_agg['price_sum'].to_numpy(); freight_sum=item_agg['freight_sum'].to_numpy()
    item_df=items.merge(products[['product_id','category_en','weight_g','volume_cm3','photos_qty']],on='product_id',how='left')
    # Delivery behavior and correlated ratings for a more realistic demo.
    planned_days=rng.integers(7,25,n_orders)
    delays=np.round(rng.normal(-1.5,6.0,n_orders)).astype(int)
    delivered_date=pd.to_datetime(purchase)+pd.to_timedelta(planned_days+delays,unit='D')
    estimated=pd.to_datetime(purchase)+pd.to_timedelta(planned_days,unit='D')
    delivered_mask=statuses=='delivered'
    delivered_date=pd.Series(delivered_date).where(delivered_mask,pd.NaT)
    estimated_date=pd.Series(estimated).where(delivered_mask,pd.NaT)
    late=((delivered_date>estimated_date)&delivered_mask).astype(int)
    base_score=rng.choice([1,2,3,4,5],n_orders,p=[.045,.055,.10,.24,.56]).astype(float)
    score=base_score.copy(); score[late==1]=np.maximum(1,score[late==1]-rng.choice([0,1],(late==1).sum(),p=[.3,.7]))
    score=np.where(delivered_mask & (rng.random(n_orders)<0.88),score,np.nan)
    is_repeat_counts=pd.Series(customer_ids).value_counts()
    payment_types=rng.choice(['credit_card_amt','debit_card_amt','boleto_amt','voucher_amt'],n_orders,p=[.72,.08,.17,.03])
    totals=price_sum+freight_sum
    payment_cols={c:np.zeros(n_orders) for c in ['credit_card_amt','debit_card_amt','boleto_amt','voucher_amt','not_defined_amt']}
    installs=rng.integers(1,13,n_orders)
    for i,t in enumerate(totals):
        payment_cols[payment_types[i]][i]=t
    payments=pd.DataFrame({'order_id':order_ids,**payment_cols,'total_payment':totals,'max_installments':installs,'payment_rows':np.ones(n_orders,dtype=int)})
    order_360=pd.DataFrame({
        'order_id':order_ids,'customer_id':[f'CUSTOMER{i:06d}' for i in cust_idx], 'customer_unique_id':customer_ids,
        'customer_state':customer_state,'order_status':statuses,'purchase_month':pd.to_datetime(purchase).strftime('%Y-%m'),
        'purchase_dt':purchase,'approved_dt':pd.to_datetime(purchase)+pd.to_timedelta(rng.integers(0,2,n_orders),unit='D'),
        'carrier_dt':pd.to_datetime(purchase)+pd.to_timedelta(rng.integers(1,5,n_orders),unit='D'),
        'delivered_dt':delivered_date,'estimated_dt':estimated_date,'date_issue':0,
        'n_items':item_agg['n_items'],'n_sellers':item_agg['n_sellers'],
        'price_sum':price_sum,'freight_sum':freight_sum,'revenue':totals,
        **payment_cols,'total_payment':totals,'max_installments':installs,'payment_rows':1,
        'review_score':score,'n_reviews':np.where(pd.notna(score),1,0),'has_items':1,
        'is_delivered':delivered_mask.astype(int),'payment_mismatch':(rng.random(n_orders)<0.0025).astype(int),
        'in_delivery_kpi':delivered_mask.astype(int),'delivery_days':np.where(delivered_mask,(pd.to_datetime(delivered_date)-pd.to_datetime(purchase)).dt.total_seconds()/86400,np.nan),
        'delay_days':np.where(delivered_mask,(pd.to_datetime(delivered_date)-pd.to_datetime(estimated_date)).dt.total_seconds()/86400,np.nan),
        'is_late':np.where(delivered_mask,late,np.nan),
    })
    reviews=order_360.loc[order_360['review_score'].notna(),['order_id','review_score']].copy()
    reviews['n_reviews']=1; reviews['comment_text']=''; reviews['review_created_dt']=pd.to_datetime(reviews['order_id'].map(dict(zip(order_ids,purchase))))+pd.to_timedelta(2,unit='D'); reviews['review_answered_dt']=reviews['review_created_dt']+pd.to_timedelta(1,unit='D'); reviews['review_date_issue']=0
    # customer summary derived from all orders
    customer_agg=order_360.groupby('customer_unique_id').agg(n_orders=('order_id','nunique'),n_delivered_orders=('is_delivered','sum'),revenue=('revenue','sum'),first_order_dt=('purchase_dt','min'),last_order_dt=('purchase_dt','max'),avg_review_score=('review_score','mean'),state=('customer_state','last')).reset_index()
    max_date=pd.to_datetime(order_360['purchase_dt']).max(); customer_agg['recency_days']=(max_date-pd.to_datetime(customer_agg['last_order_dt'])).dt.days; customer_agg['is_repeat']=(customer_agg['n_orders']>1).astype(int)
    seller_360=pd.DataFrame({'seller_id':seller_ids,'city':seller_cities,'state':seller_states,'zip_code':rng.integers(10000,99999,n_sellers)})
    seller_perf=items.groupby('seller_id').agg(revenue=('price','sum'),n_orders=('order_id','nunique'),n_items=('order_item_id','size')).reset_index()
    seller_360=seller_360.merge(seller_perf,on='seller_id',how='left').fillna({'revenue':0,'n_orders':0,'n_items':0})
    seller_360['avg_review_score']=4.0; seller_360['late_pct']=10.0
    geolocation=pd.DataFrame({'zip_code_prefix':rng.integers(1000,99999,350),'lat':rng.uniform(-33.7,5.2,350),'lng':rng.uniform(-73.9,-34.8,350),'n_points':rng.integers(1,20,350)})
    items=items.drop(columns=['_seller_index'])
    return {'order_360':order_360,'customer_360':customer_agg,'seller_360':seller_360,'items':items,'products':products,'reviews':reviews,'payments':payments,'geolocation':geolocation}
