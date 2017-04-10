__all__ = ['github_search']

import logging

from .cartfile import *
from .github import *
from .specification import *
from .styling import styled
from .config import *

def menu(prompt, items, formatter=None, default=None):
    formatter = formatter or str
    for index, item in enumerate(items):
        print('{}: {}'.format(index + 1, formatter(item)))
    while True:
        s = raw_input('>')
        if not s and default is not None:
            return default
        else:
            try:
                index = int(s)
                return items[index - 1]
            except KeyboardInterrupt:
                raise
            except:
                continue

def github_search(punic, name, cartfile_append = True, language='swift'):
    repositories = GitHub().search(name, language = language)

    logging.info('Found {} repositories matching \'{}\'. Filtering...'.format(len(repositories), name))


    # Get rid of forks.
    repositories = [repo for repo in repositories if not repo.json['fork']]

    # Get rid of zero stars.
    repositories = [repo for repo in repositories if repo.json['stargazers_count']]

    # Limit to 10 items
    repositories = repositories[:10]

    def formatter(repo):
        s = '<ref>{repo.full_name}</ref>, stars: {repo.stargazers_count}, license: {repo.license}'.format(repo=repo)
        return styled(s)

    if not cartfile_append:

        for repository in repositories:
            logging.info(formatter(repository))

    else:
        # Get rid of no license.
        repositories = [repo for repo in repositories if repo.license]

        repository = menu('?', repositories, formatter)[0]

        append_to_cartfile(punic, repository)

def append_to_cartfile(punic, repository):

    cartfile_path = config.root_path / 'Cartfile'
    if cartfile_path.exists():
        cartfile = Cartfile()
        specifications = cartfile.read(cartfile_path)
    else:
        specifications = []

    project_identifier = ProjectIdentifier(source='github', team_name=repository.owner, project_name=repository.name)
    for specification in specifications:
        if specification.identifier == project_identifier:
            logging.warning('Project \'<ref>{}</ref>\' already in cartfile'.format(project_identifier))
            return

    logging.info('Adding \'<ref>{}</ref>\' to Cartfile'.format(project_identifier))

    new_specification = Specification(identifier=project_identifier, predicate=None)
    cartfile = Cartfile(specifications + [new_specification])
    cartfile.write(cartfile_path.open('w'))
