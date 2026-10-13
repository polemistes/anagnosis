# WorkManager 2.9 (brought by Play Asset Delivery) creates its Room database by reflection, which
# R8 cannot see: without this the release build crashes at start ("Failed to create an instance of
# class androidx.work.impl.WorkDatabase").
-keep class * extends androidx.room.RoomDatabase { <init>(); }
