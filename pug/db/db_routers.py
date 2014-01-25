# db_routers.py


def is_orig(model):
    return model._meta.object_name.endswith('Orig') or model._meta.db_table.endswith('Orig')


class AppRouter(object):
    """
    Route all queries to self._apps to their own db_alias by the same name.
    """
    # Django apps with their own database with a db_alias that is the same as the app __package__ name 
    _apps = ('ssg', 'ssg_orig', 'crawler', 'miner')

    def db_for_read(self, model, **hints):
        """
        If the app has its own database, use it for reads
        """
        if model._meta.app_label in self._apps:
            return model._meta.app_label
        return None

    def db_for_write(self, model, **hints):
        """
        If the app has its own database, use it for writes
        """
        if model._meta.app_label in self._apps:
            return model._meta.app_label
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations only if both models are in the same DB
        """
        if obj1._meta.app_label == obj2._meta.app_label:
           return True
        return None

    def allow_migrate(self, db, model):
        """
        Make sure self._apps go to their own db
        """
        if db in self._apps:
            return model._meta.app_label == db
        elif model._meta.app_label in self._apps:
            return False
        return None


class OrigRouter(object):
    """
    A router to direct ...Orig models.
    """
    def db_for_read(self, model, **hints):
        if is_orig(model):
            return 'orig'
        return None

    def db_for_write(self, model, **hints):
        """Do not allow writes to Orig database"""
        if is_orig(model):
            return 'orig'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._state.db == obj2._state.db:
           return True
        return None

    def allow_migrate(self, db, model):
        if is_orig(model) and model.obj1._state.db == 'orig':
            return True
        # this router has no opinion about the existence of tables for models in this db
        return None  

