from typing import Dict, List
import os
import re


def _load_reviews() -> Dict[str, List[Dict[str, object]]]:
	"""Load hotel reviews from database.md"""
	db_path = os.path.join(os.path.dirname(__file__), "database.md")
	reviews = {}

	if not os.path.exists(db_path):
		raise FileNotFoundError(f"Database file not found: {db_path}")

	with open(db_path, 'r') as f:
		content = f.read()

	# Extract Hotel Reviews section
	reviews_section = re.search(r'## Hotel Reviews\n(.*?)\n## ', content, re.DOTALL)
	if not reviews_section:
		raise ValueError("Hotel Reviews section not found in database.md")

	review_blocks = re.findall(r'### (\w+)\n((?:- .+\n?)*)', reviews_section.group(1))

	for hotel_id, details_text in review_blocks:
		reviews[hotel_id] = []
		lines = details_text.strip().split('\n')
		i = 0
		while i < len(lines):
			if lines[i].startswith('- rating:'):
				rating = float(lines[i].split(': ')[1])
				if i + 1 < len(lines) and lines[i + 1].startswith('- comment:'):
					comment = lines[i + 1].split(': ', 1)[1]
					reviews[hotel_id].append({"rating": rating, "comment": comment})
					i += 2
				else:
					i += 1
			else:
				i += 1

	return reviews


def _load_theme_keywords() -> Dict[str, List[str]]:
	"""Load theme keywords from database.md"""
	db_path = os.path.join(os.path.dirname(__file__), "database.md")

	if not os.path.exists(db_path):
		raise FileNotFoundError(f"Database file not found: {db_path}")

	with open(db_path, 'r') as f:
		content = f.read()

	# Extract Theme Keywords section
	keywords_section = re.search(r'## Theme Keywords\n(.*?)$', content, re.DOTALL)
	if not keywords_section:
		raise ValueError("Theme Keywords section not found in database.md")

	theme_keywords = {}
	lines = keywords_section.group(1).strip().split('\n')
	for line in lines:
		if line.startswith('|') and not line.startswith('| Theme'):
			parts = [p.strip() for p in line.split('|')[1:-1]]
			if len(parts) == 2:
				theme, keywords = parts
				theme_keywords[theme] = [k.strip() for k in keywords.split(',')]

	return theme_keywords


HOTEL_REVIEWS = _load_reviews()
THEME_KEYWORDS = _load_theme_keywords()


def _extract_top_themes(comments: List[str]) -> List[str]:
	joined = " ".join(c.lower() for c in comments)
	scores: Dict[str, int] = {}

	for theme, keywords in THEME_KEYWORDS.items():
		scores[theme] = sum(joined.count(keyword) for keyword in keywords)

	ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
	return [theme for theme, score in ranked if score > 0][:3]


def get_hotel_reviews(hotel_id: str) -> str:
	"""
	Return a compact summary of customer reviews for a hotel.

	Args:
		hotel_id: Hotel identifier (for example: HCM001, HAN002, DAD003).

	Returns:
		A text summary containing average rating and key review themes.
	"""
	if not hotel_id:
		return "Invalid hotel_id. Please provide a non-empty hotel id."

	normalized_id = hotel_id.strip().upper()
	reviews = HOTEL_REVIEWS.get(normalized_id)

	if not reviews:
		return f"No review data found for hotel_id={normalized_id}."

	ratings = [float(item["rating"]) for item in reviews]
	comments = [str(item["comment"]) for item in reviews]

	average_rating = sum(ratings) / len(ratings)
	top_themes = _extract_top_themes(comments)
	theme_text = ", ".join(top_themes) if top_themes else "general satisfaction"

	sample_comments = comments[:2]
	sample_text = " | ".join(sample_comments)

	return (
		f"Hotel {normalized_id}: average rating {average_rating:.1f}/5 from {len(reviews)} reviews. "
		f"Common themes: {theme_text}. "
		f"Sample feedback: {sample_text}"
	)
