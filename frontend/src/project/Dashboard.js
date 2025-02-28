import React from 'react';
import { withNamedStores } from '../store/state';
import PropTypes from 'prop-types';

function Dashboard(props) {
  return (
    <div className="p-4">
      <img src="logo.svg" className="p-2 w-25 h-50 m-auto" alt="Logo" />
      <div className="display-3">
        Welcome {props.user.display_name}
      </div>
    </div>
  );
}

Dashboard.propTypes = {
  user: PropTypes.shape({
    display_name: PropTypes.string.isRequired,
  })
}

export default withNamedStores(Dashboard, ['user']);