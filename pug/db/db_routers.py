# db_routers.py
MS_apps = ('warranty', 'refurb')



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
    A router to direct ...Orig models to the BigData database.
    """
    def db_for_read(self, model, **hints):
        if is_orig(model):
            return 'orig'
        return None

    def db_for_write(self, model, **hints):
        """Do not allow writes to BigData (Orig) database"""
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


# def is_warranty(model):
#     # only application allowed to access MSSQL Server with Warranty data is the warranty app
#     if model._meta.app_label == 'warranty':
#         for prefix in ('Sharp', 'Warranty', 'Npc'):
#             if model._meta.object_name.startswith(prefix) or model._meta.db_table.startswith(prefix):
#                 return True
#     return False


class MSRouter(object):
    """
    A router to direct ...Orig models to the BigData database.
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label in MS_apps:
            return model._meta.app_label
        # if is_warranty(model):
        #     return 'warranty'
        return None

    def db_for_write(self, model, **hints):
        """Do not allow writes to BigData (Orig) database"""
        if model._meta.app_label in MS_apps:
            return model._meta.app_label
        # if is_warranty(model):
        #     return 'warranty'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label in MS_apps and obj2._meta.app_label in MS_apps and obj1._state.db == obj2._state.db:
           return True
        return None

    def allow_migrate(self, db, model):
        # http://stackoverflow.com/a/8502309/623735
        # south can always migrate, no matter where it is
        if model._meta.app_label == 'south':
            return True
        if model._meta.app_label in MS_apps:
            if db in MS_apps:
                return True
            return False
        return None


    # def allow_migrate(self, db, model):
    #     if model._meta.app_label in MS_apps and model.obj1._state.db == model._meta.app_label:
    #         return True
    #     # if is_warranty(model) and model.obj1._state.db == 'warranty':
    #     #     return True
    #     return None


# def is_refurb(model):
#     # only application allowed to access MSSQL Server with Warranty data is the refurb app
#     if model._meta.app_label == 'refurb':
#         for prefix in ('Refurb',):
#             if model._meta.object_name.startswith(prefix):  # or model._meta.db_table.startswith(prefix):
#                 return True
#     return False


# class RefurbMSRouter(object):
#     """
#     A router to direct ...Orig models to the BigData database.
#     """
#     def db_for_read(self, model, **hints):
#         if is_refurb(model):
#             return 'refurb'
#         return None

#     def db_for_write(self, model, **hints):
#         """Do not allow writes to BigData (Orig) database"""
#         if is_refurb(model):
#             return 'refurb'
#         return None

#     def allow_relation(self, obj1, obj2, **hints):
#         if obj1._state.db == obj2._state.db:
#            return True
#         return None

#     def allow_migrate(self, db, model):
#         #return False
#         if is_refurb(model) or model.obj1._state.db == 'refurb':
#             return True
#         return None
