%define gitver   .git.%(date +"%Y%m%d")
%define name     task-queue
%define version  1.0
%define release  1.dlts%{?gitver}%{?dist}
%define dlibdir  /usr/local/dlib/%{name}
%define _unitdir /usr/lib/systemd/system

Summary:        Run jobs in parallel using RabbitMQ.
Name:           %{name}
Version:        %{version}
Release:        %{release}
License:        NYU DLTS
Vendor:         NYU DLTS (rasan@nyu.edu)
Group:          System Environment/Daemons
URL:            https://github.com/rrasch/%{name}
%if %{!?_without_ruby:1}%{?_without_ruby:0}
Source:         task-queue-ruby.tar.bz2
%endif
BuildRoot:      %{_tmppath}/%{name}-root
# BuildArch:      noarch
%if 0%{?fedora} > 0 || 0%{?centos} > 0
BuildRequires:  git
%endif

%description
%{summary}

%prep

%build

%install
rm -rf %{buildroot}

git clone %{url}.git %{buildroot}%{dlibdir}
cd  %{buildroot}%{dlibdir}
# rm -rf %{buildroot}%{dlibdir}/.git*
find %{buildroot}%{dlibdir} -type d | xargs chmod 0755
find %{buildroot}%{dlibdir} -type f | xargs chmod 0644
find %{buildroot}%{dlibdir} -regextype posix-extended \
        -regex '.*\.(pl|rb)' | xargs chmod 0755

mkdir -p %{buildroot}%{_bindir}
ln -s %{dlibdir}/add-mb-job.pl %{buildroot}%{_bindir}/add-mb-job
ln -s %{dlibdir}/check-job-status.rb \
	%{buildroot}%{_bindir}/check-job-status
ln -s %{dlibdir}/log-job-status.rb \
	%{buildroot}%{_bindir}/log-job-status

install -D -m 0644 doc/%{name}.service %{buildroot}%{_unitdir}/%{name}.service
install -D -m 0644 doc/%{name}.cron %{buildroot}/etc/cron.d/%{name}
install -D -m 0755 workersctl %{buildroot}%{_initrddir}/%{name}
install -D -m 0644 conf/logrotate.conf %{buildroot}/etc/logrotate.d/taskqueue

mkdir -p -m 0700 %{buildroot}%{_var}/lib/%{name}

%if %{!?_without_ruby:1}%{?_without_ruby:0}
chmod 0755 %{buildroot}%{dlibdir}/rubywrap
find . -name '*.rb' | xargs perl -pi -e \
        "s,#!/usr/bin/env ruby,#!%{dlibdir}/rubywrap,"
mkdir -p %{buildroot}%{dlibdir}/ruby
tar -jvxf %{SOURCE0} -C %{buildroot}%{dlibdir} \
        --exclude=doc \
        --exclude=gem_make.out \
        --exclude='*.log' \
        --exclude=executable-hooks-uninstaller
%endif

%pre
if [ "$1" = "2" ]; then
  if [ -f /etc/redhat-release ]; then
    if [[ -n `grep -i fedora /etc/redhat-release` && `cat /etc/redhat-release|sed 's/[^0-9]*\([0-9]\+\).*/\1/'` -gt 14 ]] || [[ -n `grep -i CentOS /etc/redhat-release` && `cat /etc/redhat-release | cut -d"." -f1|sed 's/[^0-9]*\([0-9]\+\).*/\1/'` -gt 6 ]]; then
      service task-queue stop
    else
      /etc/init.d/task-queue stop
    fi
  else
    /etc/init.d/task-queue stop
  fi
fi
exit 0

%post
# Check if release is systemd based and add plex service accordingly.
if [ -f /etc/redhat-release ]; then
  if [[ -n `grep -i fedora /etc/redhat-release` && `cat /etc/redhat-release|sed 's/[^0-9]*\([0-9]\+\).*/\1/'` -lt 15 ]] || [[ -n `grep -i CentOS /etc/redhat-release` && `cat /etc/redhat-release | cut -d"." -f1|sed 's/[^0-9]*\([0-9]\+\).*/\1/'` -lt 7 ]]; then
     chkconfig --add task-queue
  else
     systemctl enable task-queue.service
     systemctl daemon-reload
  fi
fi
echo <<EOF
********************************************************************
    Please read

    %{dlibdir}/doc/INSTALL.md

    for post-installation instructions.
********************************************************************
EOF

%preun
if [ "$1" = "0" ]; then
  if [ -f /etc/redhat-release ]; then
    if [[ -n `grep -i fedora /etc/redhat-release` && `cat /etc/redhat-release|sed 's/[^0-9]*\([0-9]\+\).*/\1/'` -gt 14 ]] || [[ -n `grep -i CentOS /etc/redhat-release` && `cat /etc/redhat-release | cut -d"." -f1|sed 's/[^0-9]*\([0-9]\+\).*/\1/'` -gt 6 ]]; then
      service task-queue stop
    else
      /etc/init.d/task-queue stop
    fi
  else
    /etc/init.d/task-queue stop
  fi
fi

if [ "$1" = "0" ]; then
  if [ -f /etc/redhat-release ]; then
    if [[ -n `grep -i fedora /etc/redhat-release` && `cat /etc/redhat-release|sed 's/[^0-9]*\([0-9]\+\).*/\1/'` -lt 15 ]] || [[ -n `grep -i CentOS /etc/redhat-release` && `cat /etc/redhat-release | cut -d"." -f1|sed 's/[^0-9]*\([0-9]\+\).*/\1/'` -lt 7 ]]; then
      chkconfig --del task-queue
    else
      systemctl disable task-queue.service
      systemctl daemon-reload
    fi
  fi
else
  if [ -f /etc/redhat-release ]; then
    if [[ -n `grep -i fedora /etc/redhat-release` && `cat /etc/redhat-release|sed 's/[^0-9]*\([0-9]\+\).*/\1/'` -gt 14 ]] || [[ -n `grep -i CentOS /etc/redhat-release` && `cat /etc/redhat-release | cut -d"." -f1|sed 's/[^0-9]*\([0-9]\+\).*/\1/'` -gt 6 ]]; then
      systemctl enable task-queue
      systemctl daemon-reload
    fi
  fi
fi

%postun


%clean
rm -rf %{buildroot}

%files
%defattr(-, root, root)
%attr(-,deploy,deploy) %{dlibdir}
%{_bindir}/*
%{_unitdir}/*
%{_initrddir}/*
/etc/cron.d/%{name}
/etc/logrotate.d/taskqueue
%attr(0770,deploy,rstar) %{_var}/lib/%{name}

%changelog

# vim: et nowrap: