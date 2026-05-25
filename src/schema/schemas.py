from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List, Union
from datetime import date

class Evidence(BaseModel):
    text: str = Field(description="支持字段判断的公告原文片段")
    page_no: Optional[int] = Field(default=None, description="证据所在页码")

class ConvertibleBondBase(BaseModel):
    doc_id: str = Field(description="唯一标识单份公告，用于溯源匹配")
    stock_code: str = Field(description="标识上市公司主体")
    stock_name: str = Field(description="对应上市公司全称")
    bond_code: Optional[str] = Field(default=None, description="可转债唯一代码")
    bond_name: Optional[str] = Field(default=None, description="可转债简称")
    ann_type: str = Field(description="区分下修类/强赎类细分公告")
    publish_date: Optional[str] = Field(default=None, description="公告发布日期，格式YYYY-MM-DD")
    evidence_page: Optional[int] = Field(default=None, description="关键信息所在PDF页码")
    evidence_text: Optional[str] = Field(default=None, description="抽取内容对应的公告原文")
    notes: Optional[str] = Field(default=None, description="备注信息")

class ConversionPriceAdjustment(BaseModel):
    doc_id: str = Field(description="唯一标识单份公告")
    stock_code: str = Field(description="正股代码")
    stock_name: str = Field(description="正股名称")
    bond_code: Optional[str] = Field(default=None, description="转债代码")
    bond_name: Optional[str] = Field(default=None, description="转债名称")
    ann_type: str = Field(description="下修细分类型")
    publish_date: Optional[str] = Field(default=None, description="公告日期")
    trigger_rule: Optional[str] = Field(default=None, description="转股价下修的市场价格触发条件")
    original_conv_price: Optional[float] = Field(default=None, ge=0, description="修正前转股价格")
    new_conv_price: Optional[float] = Field(default=None, ge=0, description="修正后转股价格")
    pricing_base_date: Optional[str] = Field(default=None, description="定价基准日")
    avg_price_20d: Optional[float] = Field(default=None, description="前20日均价")
    avg_price_1d: Optional[float] = Field(default=None, description="前1日均价")
    effective_date: Optional[str] = Field(default=None, description="生效日期")
    adjustment_ratio: Optional[float] = Field(default=None, ge=0, le=100, description="下修幅度百分比")
    adjustment_type: Optional[str] = Field(default=None, description="调整类型：主动下修/被动调整")
    evidence_page: Optional[int] = Field(default=None, description="证据页码")
    evidence_text: Optional[str] = Field(default=None, description="证据原文")
    notes: Optional[str] = Field(default=None, description="备注信息")

    @field_validator('new_conv_price')
    @classmethod
    def validate_price_limit(cls, v, values):
        if v is not None:
            avg_20d = values.data.get('avg_price_20d')
            avg_1d = values.data.get('avg_price_1d')
            if avg_20d and v < avg_20d:
                raise ValueError(f"新转股价({v})低于前20日均价({avg_20d})")
            if avg_1d and v < avg_1d:
                raise ValueError(f"新转股价({v})低于前1日均价({avg_1d})")
        return v

class EarlyRedemption(BaseModel):
    doc_id: str = Field(description="唯一标识单份公告")
    stock_code: str = Field(description="正股代码")
    stock_name: str = Field(description="正股名称")
    bond_code: Optional[str] = Field(default=None, description="转债代码")
    bond_name: Optional[str] = Field(default=None, description="转债名称")
    ann_type: str = Field(description="强赎细分类型")
    publish_date: Optional[str] = Field(default=None, description="公告日期")
    redemption_trigger: Optional[str] = Field(default=None, description="提前强赎的价格天数触发规则")
    redemption_price: Optional[float] = Field(default=None, ge=100, description="可转债每张含利息赎回定价")
    record_date: Optional[str] = Field(default=None, description="股权赎回登记截止日期")
    last_convert_date: Optional[str] = Field(default=None, description="投资者最后转股操作截止日")
    delisting_date: Optional[str] = Field(default=None, description="摘牌日期")
    premium_rate: Optional[float] = Field(default=None, description="赎回溢价率")
    evidence_page: Optional[int] = Field(default=None, description="证据页码")
    evidence_text: Optional[str] = Field(default=None, description="证据原文")
    notes: Optional[str] = Field(default=None, description="备注信息")

class EventChain(BaseModel):
    bond_code: str = Field(description="转债代码")
    bond_name: str = Field(description="转债名称")
    event_type: Literal['adjustment', 'redemption'] = Field(description="事件类型")
    complete: bool = Field(description="事件链是否完整")
    nodes: List[str] = Field(description="包含的节点")
    missing_nodes: List[str] = Field(default=[], description="缺失的节点")
    trigger_date: Optional[str] = Field(default=None, description="触发日期")
    proposal_date: Optional[str] = Field(default=None, description="提议日期")
    resolution_date: Optional[str] = Field(default=None, description="决议日期")
    implementation_date: Optional[str] = Field(default=None, description="实施日期")
    total_days: Optional[int] = Field(default=None, description="事件周期天数")
    cycle_status: Literal['NORMAL', 'LONG', 'SHORT'] = Field(default='NORMAL', description="周期状态")
    original_conv_price: Optional[float] = Field(default=None, description="原转股价")
    new_conv_price: Optional[float] = Field(default=None, description="新转股价")
    adjustment_ratio: Optional[float] = Field(default=None, description="下修幅度")
    redemption_price: Optional[float] = Field(default=None, description="赎回价格")
    premium_rate: Optional[float] = Field(default=None, description="赎回溢价率")