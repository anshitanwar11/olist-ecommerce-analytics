"""Streamlit-cached access to the project data and the delivered-order base table."""
import streamlit as st
from src import data_loader, dashboard


@st.cache_resource(show_spinner="Loading the eight cleaned Olist tables...")
def get_data():
    return data_loader.load_all()


@st.cache_resource(show_spinner="Preparing orders...")
def get_orders():
    return dashboard.base_orders(get_data())
