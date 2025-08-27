class VersionError(Exception):
    pass


class CrossPlatformValidator:
    def __init__(self):
        pass
    
    def validate_parity(self, android_schema, ios_schema):
        android_version = android_schema.get('version')
        ios_version = ios_schema.get('version')
        
        if android_version != ios_version:
            raise VersionError(f"Schema version mismatch: Android {android_version} != iOS {ios_version}")
        
        return {"parity": True}