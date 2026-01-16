import uuid

from datetime import datetime, timezone
from typing import Any, Optional, Tuple

from app.extensions import db
from app.models.game.achievement import Achievement
from app.models.game.user_achievement.model import UserAchievement
from app.models.game.user_game_stats.model import UserGameStats
from app.models.game.xp_transaction.model import XPTransactionTypeEnum
from app.models.user.model import User

from app.services.xp_service import XPService


class AchievementService:
    """Service for managing achievements"""

    @staticmethod
    def check_achievements(user_id: uuid.UUID, game_id: Optional[uuid.UUID] = None):
        """Check if user has unlocked any new achievements"""

        # Get all active achievements for this game (or platform-wide)
        query = Achievement.query.filter_by(is_active=True)

        if game_id:
            query = query.filter(
                db.or_(Achievement.game_id == game_id, Achievement.game_id.is_(None))
            )
        else:
            query = query.filter(Achievement.game_id.is_(None))

            achievements: list[Achievement] = query.all()

            unlocked = []

            for achievement in achievements:
                # Check if user already has this achievement
                user_achievement: UserAchievement | None = (
                    UserAchievement.query.filter_by(
                        user_id=user_id, achievement_id=achievement.id
                    ).first()
                )

                if user_achievement and user_achievement.unlocked_at:
                    continue

                # Check if requirements are met
                is_unlocked, progress = AchievementService._check_requirement(
                    user_id=user_id,
                    requirement_def=achievement.requirement_definition,
                    game_id=game_id,
                )

                if not user_achievement:
                    # Create tracking record
                    user_achievement = UserAchievement(
                        user_id=user_id,
                        achievement_id=achievement.id,
                        progress=progress,
                    )
                    db.session.add(user_achievement)
                else:
                    # Update progress
                    user_achievement.progress = progress

                if is_unlocked:
                    # Unlock achievement
                    user_achievement.unlocked_at = datetime.now(timezone.utc)

                    # Increment unlock count
                    achievement.unlock_count += 1

                    # Award XP
                    if achievement.xp_reward > 0:
                        XPService.award_xp(
                            user_id=user_id,
                            amount=achievement.xp_reward,
                            transaction_type=XPTransactionTypeEnum.ACHIEVEMENT,
                            game_id=game_id,
                            reference_id=achievement.id,
                            meta={
                                "achievement_name": achievement.name,
                            },
                        )

                    unlocked.append(achievement)

                db.session.commit()

                return unlocked

    @staticmethod
    def _check_requirement(
        user_id: uuid.UUID,
        requirement_def: dict[str, Any],
        game_id: Optional[uuid.UUID] = None,
    ) -> Tuple[bool, dict[str, Any]]:
        """
        Check if user meets achievement requirement
        Returns: (is_unlocked: bool, progress: dict)
        """

        req_type = requirement_def.get("type")

        if req_type == "stat_threshold":
            stat_name = requirement_def.get("stat")
            threshold = requirement_def.get("threshold")

            if threshold or not isinstance(threshold, "int"):
                return False, {"current": 0, "required": 0}

            if not stat_name:
                return False, {"current": 0, "required": threshold}

            if game_id:
                stats: UserGameStats | None = UserGameStats.query.filter_by(
                    user_id=user_id,
                    game_id=game_id,
                ).first()

                if not stats:
                    return False, {"current": 0, "required": threshold}

                stat_value = getattr(stats, stat_name, 0)
            else:
                # Platform-wide stat
                user = User.query.get(user_id)
                stat_value = getattr(user, stat_name, 0)

            progress = {
                "current": stat_value,
                "required": threshold,
                "percentage": min(100, int((stat_value / threshold) * 100)),
            }

            return stat_value >= threshold, progress

        elif req_type == "custom_stat":
            stat_name = requirement_def.get("stat")
            threshold = requirement_def.get("threshold")

            stats: UserGameStats | None = UserGameStats.query.filter_by(
                user_id=user_id,
                game_id=game_id,
            ).first()

            if not stats or not stats.custom_stats:
                return False, {"current": 0, "required": threshold}

            stat_value = stats.custom_stats.get(stat_name, 0)

            progress = {
                "current": stat_value,
                "required": threshold,
                "percentage": min(100, int((stat_value / threshold) * 100)),
            }

            return stat_value >= threshold, progress

        elif req_type == "score_threshold":
            score_threshold = requirement_def.get("score")

            stats: UserGameStats | None = UserGameStats.query.filter_by(
                user_id=user_id,
                game_id=game_id,
            ).first()

            if not stats:
                return False, {"current": 0, "required": score_threshold}

            progress = {
                "current": stats.best_score,
                "required": score_threshold,
                "percentage": min(100, int((stats.best_score / score_threshold) * 100)),
            }

            return stats.best_score >= score_threshold, progress

        elif req_type == "streak":
            streak_days = requirement_def.get("days")

            stats = UserGameStats.query.filter_by(
                user_id=user_id,
                game_id=game_id,
            ).first()

            if not stats:
                return False, {"current": 0, "required": streak_days}

            current_streak = stats.current_streak
            progress = {
                "current": current_streak,
                "required": streak_days,
                "percentage": min(100, int((current_streak / streak_days) * 100)),
            }

            return current_streak >= streak_days, progress

        return False, {}

    @staticmethod
    def get_user_achievements(
        user_id: uuid.UUID, game_id: Optional[uuid.UUID], unlocked_only=False
    ):
        """Get achievements for a user"""
        query = (
            db.session.query(Achievement, UserAchievement)
            .outerjoin(
                UserAchievement,
                db.and_(
                    Achievement.id == UserAchievement.achievement_id,
                    UserAchievement.user_id == user_id,
                ),
            )
            .filter(Achievement.is_active)
        )

        if game_id:
            query = query.filter(
                db.or_(Achievement.game_id == game_id, Achievement.game_id.is_(None))
            )

        if unlocked_only:
            query = query.filter(UserAchievement.unlocked_at.isnot(None))

        return query.all()
