import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Changed relation from res.partner to res.users.
    # We need to unlink partner ids where operator_id is not null.
    cr.execute("""UPDATE forest_tree_felling SET operator_id=null WHERE operator_id IS NOT NULL;""")

    _logger.info("Updated forest_tree_felling operator_id relation.")
