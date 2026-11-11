"""EdgeBet AI - Polymorphic Multi-Sport Database Schema & Data Models.

Defines the relational SQL / NoSQL JSONB and Pydantic models for:
- Sports & Categories
- Competitions / Tournaments (Hierarchical Tree)
- Polymorphic Events & Fixtures
- Sport-Specific Statistical Payloads (JSONB)
- Multi-Bookmaker Odds & 20-Min Rolling Snapshots (Dropping Odds)
- Predictions, +EV Discovery & User Entitlements (Stripe/SaaS)
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. Enums
# ---------------------------------------------------------------------------

class SportType(str, Enum):
    FOOTBALL = "football"
    TENNIS = "tennis"
    FORMULA1 = "f1"
    MOTOGP = "motogp"
    NFL = "nfl"
    BASKETBALL = "basketball"
    RUGBY = "rugby"
    CROSS_SPORT = "all"

class EventStatus(str, Enum):
    PRE_MATCH = "pre"
    IN_PLAY = "live"
    COMPLETED = "post"
    POSTPONED = "postponed"

class MarketFamily(str, Enum):
    RESULT_1X2 = "1x2"
    MONEYLINE = "moneyline"
    DOUBLE_CHANCE = "double_chance"
    OVER_UNDER = "over_under"
    HANDICAP_SPREAD = "handicap"
    BOTH_TEAMS_SCORE = "btts"
    HEAD_TO_HEAD_DUEL = "driver_h2h"
    PODIUM_TOP3 = "podium"
    PLAYER_PROPS = "player_props"
    MARGIN_VICTORY = "margin"


# ---------------------------------------------------------------------------
# 2. Sport-Specific Polymorphic Statistical Payloads (JSONB in SQL)
# ---------------------------------------------------------------------------

class FootballSpecificStats(BaseModel):
    xg_home: float = Field(..., description="Expected Goals for Home team")
    xg_away: float = Field(..., description="Expected Goals for Away team")
    corners_proj_total: float = Field(..., description="Projected corners based on attacking pitch width")
    cards_proj_total: float = Field(..., description="Projected yellow/red cards based on referee severity")
    referee_name: Optional[str] = None
    referee_cards_per_game: Optional[float] = None
    confirmed_lineups: bool = False
    half_time_goals_proj: float = 1.15

class TennisSpecificStats(BaseModel):
    surface: str = Field(..., description="Clay, Hard (Indoor/Outdoor), Grass")
    serve_win_pct_a: float
    serve_win_pct_b: float
    bp_saved_pct_a: float
    bp_saved_pct_b: float
    minutes_played_prior_a: int = Field(0, description="Accumulated tournament fatigue in minutes")
    minutes_played_prior_b: int = 0
    h2h_wins_a: int = 0
    h2h_wins_b: int = 0
    tiebreak_prob: float = 0.25

class MotorsportSpecificStats(BaseModel):
    circuit_name: str
    laps: int
    asphalt_temperature_c: float
    rain_probability_pct: float
    fp_pace_delta_telemetry: float = Field(..., description="Lap delta (s) across FP2 long runs")
    tire_deg_coefficient: float = Field(..., description="Tire degradation (s/lap) for lead stint")
    safety_car_probability: float = 0.45
    lead_h2h_duel_name: str = "Driver A vs Driver B"

class NFLSpecificStats(BaseModel):
    yards_per_play_off_home: float
    yards_per_play_def_away: float
    turnover_differential: int
    qb_name_home: str
    qb_name_away: str
    qb_injury_status_home: str = "Healthy"
    qb_injury_status_away: str = "Healthy"
    weather_wind_mph: float = 8.0
    weather_precipitation: str = "Clear"

class BasketballSpecificStats(BaseModel):
    game_pace_possessions: float = Field(..., description="Projected 48-min possessions")
    offensive_rating_home: float
    defensive_rating_away: float
    is_back_to_back_home: bool = False
    is_back_to_back_away: bool = False

class RugbySpecificStats(BaseModel):
    scrum_win_pct_diff: float = Field(..., description="Scrum set-piece differential %")
    lineout_win_pct_diff: float
    penalties_conceded_avg_home: float
    penalties_conceded_avg_away: float
    sin_bin_yellow_risk: str = "Moderate"


# ---------------------------------------------------------------------------
# 3. Core Database Entities
# ---------------------------------------------------------------------------

class Competition(BaseModel):
    id: str
    sport: SportType
    name: str
    country: str
    flag: str
    is_pinned: bool = False
    tier: int = 1
    season: str = "2025/2026"

class OddsSnapshot(BaseModel):
    bookmaker: str
    price: float
    recorded_at: datetime
    delta_20m_pct: float = 0.0

class MarketOdd(BaseModel):
    market_family: MarketFamily
    selection: str
    simulated_prob: float
    fair_odds: float
    best_bookmaker: str
    best_odds: float
    edge_pct: float
    is_dropping_odds: bool = False
    dropping_20m_pct: float = 0.0
    all_books: List[Dict[str, Any]] = []

class PolymorphicEvent(BaseModel):
    id: str
    sport: SportType
    competition_id: str
    title: str
    competitor_a: str
    competitor_b: str
    start_time: datetime
    status: EventStatus = EventStatus.PRE_MATCH
    sport_stats: Union[
        FootballSpecificStats,
        TennisSpecificStats,
        MotorsportSpecificStats,
        NFLSpecificStats,
        BasketballSpecificStats,
        RugbySpecificStats,
        Dict[str, Any]
    ]
    best_pick: Optional[MarketOdd] = None
    markets: List[MarketOdd] = []


# ---------------------------------------------------------------------------
# 4. PostgreSQL DDL Reference Schema
# ---------------------------------------------------------------------------
SQL_SCHEMA_DDL = """
-- PostgreSQL Relational Schema with JSONB Polymorphism for Multi-Sport

CREATE TABLE IF NOT EXISTS sports (
    id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    icon VARCHAR(16) NOT NULL,
    category VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS competitions (
    id VARCHAR(64) PRIMARY KEY,
    sport_id VARCHAR(32) REFERENCES sports(id),
    name VARCHAR(128) NOT NULL,
    country VARCHAR(64) NOT NULL,
    flag VARCHAR(16) NOT NULL,
    is_pinned BOOLEAN DEFAULT FALSE,
    tier SMALLINT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
    id VARCHAR(64) PRIMARY KEY,
    sport_id VARCHAR(32) REFERENCES sports(id),
    competition_id VARCHAR(64) REFERENCES competitions(id),
    title VARCHAR(256) NOT NULL,
    competitor_a VARCHAR(128) NOT NULL,
    competitor_b VARCHAR(128) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(16) DEFAULT 'pre',
    sport_specific_stats JSONB NOT NULL, -- Polymorphic JSONB: xG, Telemetry, Surface, Pace, etc.
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS odds_snapshots (
    id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(64) REFERENCES events(id) ON DELETE CASCADE,
    market_family VARCHAR(32) NOT NULL,
    selection VARCHAR(128) NOT NULL,
    bookmaker VARCHAR(64) NOT NULL,
    price NUMERIC(6, 2) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_odds_snapshots_event_time ON odds_snapshots(event_id, selection, recorded_at DESC);
CREATE INDEX idx_events_sport_time ON events(sport_id, start_time);
"""
