# coding: utf8
import datetime
import json

from flask import render_template, request, url_for

from ..myview import MyView


template_listversions_error = """
<a class="request" target="_blank" href="{url}">REQUEST</a>
<em class="fail"> got status: {status}</em>
<pre>{text}</pre>
You can <a class="button safe" href="{url_deploy}">Deploy Project</a>
with a new project name or
<a class="button danger" href="javascript:;"
onclick="execXHR('{url_delproject}', 'versions_of_{project}', 'Delete project \\'{project}\\'?');">
Delete Project
</a>
"""


class ManageView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()

        self.opt = self.view_args['opt']
        self.project = self.view_args['project']
        self.version_spider_job = self.view_args['version_spider_job']

        self.text = ''
        self.js = {}

    def dispatch_request(self, **kwargs):
        # self.text = api(self.node, self.opt, self.project, self.version_spider_job)
        _url = url_for('api', node=self.node, opt=self.opt, project=self.project,
                       version_spider_job=self.version_spider_job)  # '/1/api/listprojects/'
        self.text = self.get_response_from_view(_url)
        # _bind = '127.0.0.1' if self.SCRAPYDWEB_BIND == '0.0.0.0' else self.SCRAPYDWEB_BIND
        # _url = 'http://{}:{}{}'.format(_bind, self.SCRAPYDWEB_PORT, _url)
        # _auth = (self.USERNAME, self.PASSWORD) if self.ENABLE_AUTH else None
        # status_code, self.text = self.make_request(_url, api=False, auth=_auth)
        self.js = json.loads(self.text)

        if self.js['status'] == 'ok':
            return getattr(self, self.opt)()
        else:
            return self.handle_status_error()

    def handle_status_error(self):
        if self.opt == 'listversions':
            kwargs = dict(
                url=self.js['url'],
                status=self.js['status'],
                url_deploy=url_for('deploy.deploy', node=self.node),
                url_delproject=url_for('manage', node=self.node, opt='delproject', project=self.project),
                project=self.project,
                text=self.text
            )
            return template_listversions_error.format(**kwargs)
        else:
            if self.POST:
                # Pass request.url instead of js['url'], for GET method
                return ('<a class="request" target="_blank" href="%s">REQUEST</a>'
                        '<em class="fail"> got status: %s</em>') % (request.url, self.js['status'])
            else:
                message = self.js.get('message', '')
                if message:
                    self.js.update({'message': 'See details below'})
                return render_template(self.template_fail, node=self.node,
                                       text=self.json_dumps(self.js), message=message)

    def listprojects(self):
        results = []
        for project in self.js['projects']:
            url_listversions = url_for('manage', node=self.node, opt='listversions', project=project)
            results.append((project, url_listversions))
        if self.POST:
            url = self.js['url']
        else:
            url = self.js['url'].replace('http://', 'http://%s:%s@' % self.AUTH) if self.AUTH else self.js['url']

        kwargs = dict(
            node=self.node,
            url=url,
            node_name=self.js['node_name'],
            results=results,
            url_deploy=url_for('deploy.deploy', node=self.node)
        )
        return render_template('scrapydweb/manage.html', **kwargs)

    def listversions(self):
        results = []
        for version in self.js['versions']:
            try:
                version_readable = ' (%s)' % datetime.datetime.fromtimestamp(int(version)).isoformat()
            except:
                version_readable = ''

            url_listspiders = url_for('manage', node=self.node, opt='listspiders', project=self.project,
                                      version_spider_job=version)
            url_multinode_delversion = url_for('overview', node=self.node, opt='delversion', project=self.project,
                                               version_job=version)
            url_delversion = url_for('manage', node=self.node, opt='delversion', project=self.project,
                                     version_spider_job=version)
            results.append((version, version_readable, url_listspiders, url_multinode_delversion, url_delversion))

        kwargs = dict(
            node=self.node,
            project=self.project,
            results=results,
            url_multinode_delproject=url_for('overview', node=self.node, opt='delproject', project=self.project),
            url_delproject=url_for('manage', node=self.node, opt='delproject', project=self.project)
        )
        return render_template('scrapydweb/listversions.html', **kwargs)

    def listspiders(self):
        spiders = self.js['spiders']
        results = []
        for spider in spiders:
            url_schedule = url_for('schedule.schedule', node=self.node,
                                   project=self.project, version=self.version_spider_job, spider=spider)
            url_multinode_schedule = url_for('overview', node=self.node, opt='schedule',
                                             project=self.project, version_job=self.version_spider_job, spider=spider)
            results.append((spider, url_schedule, url_multinode_schedule))

        return render_template('scrapydweb/listspiders.html', node=self.node, results=results)

    @staticmethod
    def delversion():
        return '<em class="pass">deleted</em>'

    @staticmethod
    def delproject():
        return '<em class="pass">deleted</em>'
