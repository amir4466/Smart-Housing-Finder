"""Start the Smart Housing Agent."""

from .storage.database import initialize_database
from .settings import load_preferences


def main() -> None:
    preferences = load_preferences()
    initialize_database()

    print("Database is ready.")
    print("Loaded preferences:", preferences.city)

    print(
        f"Loaded preferences: {len(preferences.preference_criteria)} criteria")

if __name__ == "__main__":
    main()