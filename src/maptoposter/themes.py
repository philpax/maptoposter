from dataclasses import dataclass

@dataclass
class Theme:
    bg: str
    text: str
    gradient_color: str
    water: str
    parks: str
    subway: str
    tram: str
    light_rail: str
    train: str
    road: str

themes = {
    "feature_based": Theme(
        bg="#FFFFFF",
        text="#000000",
        gradient_color="#FFFFFF",
        water="#C0C0C0",
        parks="#F0F0F0",
        subway="#0A0A0A",
        tram="#1A1A1A",
        light_rail="#1A1A1A",
        train="#2A2A2A",
        road="#3A3A3A"
    ),
    "automn": Theme(
        bg="#FBF7F0",
        text="#8B4513",
        gradient_color="#FBF7F0",
        water="#D8CFC0",
        parks="#E8E0D0",
        subway="#8B2500",
        tram="#B8450A",
        light_rail="#B8450A",
        train="#D9A050",
        road="#CC7A30"
    ),
    "blueprint": Theme(
        bg="#1A3A5C",
        text="#E8F4FF",
        gradient_color="#1A3A5C",
        water="#0F2840",
        parks="#1E4570",
        subway="#E8F4FF",
        tram="#C5DCF0",
        light_rail="#C5DCF0",
        train="#9FC5E8",
        road="#7BAED4"
    ),
    "copper_patina": Theme(
        bg="#E8F0F0",
        text="#2A5A5A",
        gradient_color="#E8F0F0",
        water="#C0D8D8",
        parks="#D8E8E0",
        subway="#B87333",
        tram="#5A8A8A",
        light_rail="#5A8A8A",
        train="#6B9E9E",
        road="#88B4B4"
    ),
    "forest": Theme(
        bg="#F0F4F0",
        text="#2D4A3E",
        gradient_color="#F0F4F0",
        water="#B8D4D4",
        parks="#D4E8D4",
        subway="#2D4A3E",
        tram="#3D6B55",
        light_rail="#3D6B55",
        train="#5A8A70",
        road="#7AAA90"
    ),
    "japanese_ink": Theme(
        bg="#FAF8F5",
        text="#2C2C2C",
        gradient_color="#FAF8F5",
        water="#E8E4E0",
        parks="#F0EDE8",
        subway="#8B2500",
        tram="#4A4A4A",
        light_rail="#4A4A4A",
        train="#6A6A6A",
        road="#909090"
    ),
    "midnight_blue": Theme(
        bg="#0A1628",
        text="#D4AF37",
        gradient_color="#0A1628",
        water="#061020",
        parks="#0F2235",
        subway="#D4AF37",
        tram="#C9A227",
        light_rail="#C9A227",
        train="#A8893A",
        road="#8B7355"
    ),
    "monochrome_blue": Theme(
        bg="#F5F8FA",
        text="#1A3A5C",
        gradient_color="#F5F8FA",
        water="#D0E0F0",
        parks="#E0EAF2",
        subway="#1A3A5C",
        tram="#2A5580",
        light_rail="#2A5580",
        train="#4A7AA8",
        road="#4A7AA8"
    ),
    "neon_cyberpunk": Theme(
        bg="#0D0D1A",
        text="#00FFFF",
        gradient_color="#0D0D1A",
        water="#0A0A15",
        parks="#151525",
        subway="#FF00FF",
        tram="#00FFFF",
        light_rail="#00FFFF",
        train="#00C8C8",
        road="#0098A0"
    ),
    "noir": Theme(
        bg="#000000",
        text="#FFFFFF",
        gradient_color="#000000",
        water="#0A0A0A",
        parks="#111111",
        subway="#FFFFFF",
        tram="#E0E0E0",
        light_rail="#E0E0E0",
        train="#B0B0B0",
        road="#808080"
    ),
    "ocean": Theme(
        bg="#F0F8FA",
        text="#1A5F7A",
        gradient_color="#F0F8FA",
        water="#B8D8E8",
        parks="#D8EAE8",
        subway="#1A5F7A",
        tram="#2A7A9A",
        light_rail="#2A7A9A",
        train="#4A9AB8",
        road="#4A9AB8"
    ),
    "pastel_dream": Theme(
        bg="#FAF7F2",
        text="#5D5A6D",
        gradient_color="#FAF7F2",
        water="#D4E4ED",
        parks="#E8EDE4",
        subway="#7B8794",
        tram="#9BA4B0",
        light_rail="#9BA4B0",
        train="#B5AEBB",
        road="#C9C0C9"
    ),
    "sunset": Theme(
        bg="#FDF5F0",
        text="#C45C3E",
        gradient_color="#FDF5F0",
        water="#F0D8D0",
        parks="#F8E8E0",
        subway="#C45C3E",
        tram="#D87A5A",
        light_rail="#D87A5A",
        train="#E8A088",
        road="#E8A088"
    ),
    "terracotta": Theme(
        bg="#F5EDE4",
        text="#8B4513",
        gradient_color="#F5EDE4",
        water="#A8C4C4",
        parks="#E8E0D0",
        subway="#A0522D",
        tram="#B8653A",
        light_rail="#B8653A",
        train="#C9846A",
        road="#D9A08A"
    ),
    "warm_beige": Theme(
        bg="#F5F0E8",
        text="#6B5B4F",
        gradient_color="#F5F0E8",
        water="#DDD5C8",
        parks="#E8E4D8",
        subway="#8B7355",
        tram="#A08B70",
        light_rail="#A08B70",
        train="#B5A48E",
        road="#C9BBAA"
    )
}
